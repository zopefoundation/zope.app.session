##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
Session implementation using cookies

$Id$
"""
        
from BTrees.OOBTree import OOBTree
from heapq import heapify, heappop
from persistent import Persistent
from UserDict import DictMixin
from zope.app.annotation.interfaces import IAttributeAnnotatable
from zope.app.container.contained import Contained
from zope.app.i18n import ZopeMessageIDFactory as _
from zope.app import zapi
from zope.app.session.interfaces import IClientIdManager 
from zope.app.session.interfaces import IPersistentSessionData
from zope.app.session.interfaces import IPersistentSessionDataManager
from zope.app.utility.interfaces import ILocalUtility
from zope import schema
import random
import sha
import thread
import time
import ZODB.MappingStorage
import zope.cachedescriptors.property
import zope.interface
        

class ISessionDataConfig(zope.interface.Interface):
    """Configure session data storage"""

    sweepInterval = schema.Int(
            title=_(u"Purge Interval"),
            description=_(
                "How often stale data is purged in seconds. "
                "Higer values improve performance."
                ),
            default=5*60,
            required=True,
            min=1,
            )

class PersistentSessionDataContainer(Persistent, Contained):
    ''' A SessionDataContainer that stores data in the ZODB '''

    zope.interface.implements(
        IPersistentSessionDataManager,
        ISessionDataConfig,
        ILocalUtility,
        IAttributeAnnotatable,
        )

    def __init__(self):
        self.data = OOBTree()
        self.sweepInterval = 5*60

    _v_data = zope.cachedescriptors.property.Volatile('_v_data', dict)

    def __getitem__(self, client_id):
        """Return data for a client id

           If no data has been stored for the client id, then return
           a new PersistentSessionData object, but don't modify the
           PersistentSessionDataContainer.

           Let's look at an example:

             >>> container = PersistentSessionDataContainer()
             >>> session = container['id']
             >>> session['appid1'] = 42

           Of course, if we ask for the session data again. we'll get
           the same object:

             >>> container['id'] is session
             True

           This applies to new data, even when the container hasn't
           changed:

             >>> newsession = container['newid']
             >>> newsession is session
             False
             >>> newsession is container['newid']
             True

           The container has a sweep interval, in seconds.
           Data older than that interval is removed. To see how this
           works, we'll "age" our session object by setting it's last
           access time to a time in the distant past:

             >>> from time import time
             >>> session.lastAccessTime = (
             ...    int(time()) - container.sweepInterval * 2)

           Now, if we sk for a session, we'll get a different one:

             >>> container['id'] is session
             False

           And the data we stored before will be gone:

             >>> 'appid1' in container['id']
             False
           """
        now = time.time()
        
        rv = self.data.get(client_id)
        if rv is None:
            rv = self._v_data.get(client_id)
            if rv is None:
                rv = PersistentSessionData(self, client_id)
                rv.lastAccessTime = int(now)
                self._v_data[client_id] = rv
            
        # Only update lastAccessTime once every few minutes, rather than
        # every hit, to avoid ZODB bloat and conflicts
        if rv.lastAccessTime + self.sweepInterval < now:            
            # XXX: When scheduler exists, this method should just schedule
            # a sweep later since we are currently busy handling a request
            # and may end up doing simultaneous sweeps
            self.sweep()
            rv = PersistentSessionData(self, client_id)
            rv.lastAccessTime = int(now)
            self._v_data[client_id] = rv
            
        return rv

    def _setitem(self, client_id, session_data):
        # This method is for use by PersistentSessionData only
        if client_id in self._v_data:
            del self._v_data[client_id]
        self.data[client_id] = session_data

    def sweep(self):
        ''' Clean out stale data '''
        expire_time = time.time() - self.sweepInterval
        heap = [(v.lastAccessTime, k) for k,v in self.data.items()]
        heapify(heap)
        while heap:
            lastAccessTime, key = heappop(heap)
            if lastAccessTime < expire_time:
                del self.data[key]
            else:
                return


class RAMSessionDataContainer(PersistentSessionDataContainer):
    ''' A SessionDataContainer that stores data in RAM. Currently session
        data is not shared between Zope clients, so server affinity will
        need to be maintained to use this in a ZEO cluster.
    '''
    def __init__(self):
        self.sweepInterval = 5*60
        self.key = sha.new(str(time.time() + random.random())).hexdigest()

    _ram_storage = ZODB.MappingStorage.MappingStorage()
    _ram_db = ZODB.DB(_ram_storage)
    _conns = {}

    def _getData(self):

        # Open a connection to _ram_storage per thread
        tid = thread.get_ident()
        if not self._conns.has_key(tid):
            self._conns[tid] = self._ram_db.open()

        root = self._conns[tid].root()
        if not root.has_key(self.key):
            root[self.key] = OOBTree()
        return root[self.key]

    data = property(_getData, None)

    def sweep(self):
        super(RAMSessionDataContainer, self).sweep()
        self._ram_db.pack(time.time())


class PersistentSessionData(Persistent, DictMixin):

    zope.interface.implements(IPersistentSessionData)

    def __init__(self, manager, client_id):
        self.manager, self.client_id = manager, client_id
        self.data = {}

    _v_data = zope.cachedescriptors.property.Volatile('_v_data', dict)

    def __getitem__(self, application_key):
        r = self.data.get(application_key)
        if r is None:
            r = self._v_data.get(application_key)
            if r is None:
                r = PersistentApplicationData(self, application_key)
        return r

    def __setitem__(self, application_key, application_data):
        if self.manager is not None:
            self.manager._setitem(self.client_id, self)
            self.manager = None
        if application_key in self._v_data:
            del self._v_data[application_key]
        self.data[application_key] = application_data
        self._p_changed = 1

    def __delitem__(self, application_key):
        if application_key in self.data:
            del self.data[application_key]
        if application_key in self._v_data:
            del self._v_data[application_key]
        self._p_changed = 1

    def keys(self):
        return self.data.keys
            

class PersistentApplicationData(DictMixin):
    def __init__(self, manager, application_key):
        self.manager = manager
        self.application_key = application_key
        self.data = {}

    def __getitem__(self, key):
        return self.data[key]
        
    def __setitem__(self, key, value):
        self.manager[self.application_key] = self
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def keys(self):
        return self.data.keys()

def accessPersistentSessionData(request):
    ids = zapi.getUtility(IClientIdManager)
    client_id = ids.getClientId(request)
    manager = zapi.getUtility(IPersistentSessionDataManager)
    return manager[client_id]
