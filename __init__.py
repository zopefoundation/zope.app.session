##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
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
import sha, time, string, random, hmac, warnings, thread
from UserDict import IterableUserDict
from heapq import heapify, heappop

from persistent import Persistent
from zope.server.http.http_date import build_http_date
from zope.interface import implements
from zope.component import ComponentLookupError
from zope.app.zapi import getUtility
from BTrees.OOBTree import OOBTree
from zope.app.utility.interfaces import ILocalUtility
from zope.app.annotation.interfaces import IAttributeAnnotatable

from interfaces import \
        IBrowserIdManager, IBrowserId, ICookieBrowserIdManager, \
        ISessionDataContainer, ISession, ISessionProductData, ISessionData

import ZODB
import ZODB.MappingStorage

cookieSafeTrans = string.maketrans("+/", "-.")

def digestEncode(s):
    """Encode SHA digest for cookie."""
    return s.encode("base64")[:-2].translate(cookieSafeTrans)


class BrowserId(str):
    """See zope.app.interfaces.utilities.session.IBrowserId"""
    implements(IBrowserId)

    def __new__(cls, request):
        return str.__new__(
                cls, getUtility(IBrowserIdManager).getBrowserId(request)
                )


class CookieBrowserIdManager(Persistent):
    """Session service implemented using cookies."""

    implements(IBrowserIdManager, ICookieBrowserIdManager,
               ILocalUtility, IAttributeAnnotatable,
               )

    __parent__ = __name__ = None

    def __init__(self):
        self.namespace = "zope3_cs_%x" % (int(time.time()) - 1000000000)
        self.secret = "%.20f" % random.random()
        self.cookieLifetime = None

    def generateUniqueId(self):
        """Generate a new, random, unique id."""
        data = "%.20f%.20f%.20f" % (random.random(), time.time(), time.clock())
        digest = sha.sha(data).digest()
        s = digestEncode(digest)
        # we store a HMAC of the random value together with it, which makes
        # our session ids unforgeable.
        mac = hmac.new(s, self.secret, digestmod=sha).digest()
        return s + digestEncode(mac)

    def getRequestId(self, request):
        """Return the browser id encoded in request as a string, 
        or None if it's non-existent."""
        # If there is an id set on the response, use that but don't trust it.
        # We need to check the response in case there has already been a new
        # session created during the course of this request.
        response_cookie = request.response.getCookie(self.namespace)
        if response_cookie:
            sid = response_cookie['value']
        else:
            sid = request.cookies.get(self.namespace)
        if sid is None or len(sid) != 54:
            return None
        s, mac = sid[:27], sid[27:]
        if (digestEncode(hmac.new(s, self.secret, digestmod=sha).digest())
            != mac):
            return None
        else:
            return sid

    def setRequestId(self, request, id):
        """Set cookie with id on request."""
        # Currently, the path is the ApplicationURL. This is reasonable, and
        # will be adequate for most purposes.
        # TODO: A better path to use would be that of the folder that contains
        # the service-manager this service is registered within. However, that
        # would be expensive to look up on each request, and would have to be
        # altered to take virtual hosting into account.  Seeing as this
        # service instance has a unique namespace for its cookie, using
        # ApplicationURL shouldn't be a problem.

        if self.cookieLifetime is not None:
            if self.cookieLifetime:
                expires = build_http_date(time.time() + self.cookieLifetime)
            else:
                expires = 'Tue, 19 Jan 2038 00:00:00 GMT'
            request.response.setCookie(
                    self.namespace, id, expires=expires,
                    path=request.getApplicationURL(path_only=True)
                    )
        else:
            request.response.setCookie(
                    self.namespace, id,
                    path=request.getApplicationURL(path_only=True)
                    )

    def getBrowserId(self, request):
        """See zope.app.session.interfaces.IBrowserIdManager"""
        sid = self.getRequestId(request)
        if sid is None:
            sid = self.generateUniqueId()
        self.setRequestId(request, sid)
        return sid


class PersistentSessionDataContainer(Persistent, IterableUserDict):
    ''' A SessionDataContainer that stores data in the ZODB '''
    __parent__ = __name__ = None

    implements(ISessionDataContainer, ILocalUtility, IAttributeAnnotatable)

    def __init__(self):
        self.data = OOBTree()
        self.sweepInterval = 5*60

    def __getitem__(self, product_id):
        rv = IterableUserDict.__getitem__(self, product_id)
        now = time.time()
        # Only update lastAccessTime once every few minutes, rather than
        # every hit, to avoid ZODB bloat and conflicts
        if rv.lastAccessTime + self.sweepInterval < now:
            rv.lastAccessTime = int(now)
            # XXX: When scheduler exists, this method should just schedule
            # a sweep later since we are currently busy handling a request
            # and may end up doing simultaneous sweeps
            self.sweep()
        return rv

    def __setitem__(self, product_id, session_data):
        session_data.lastAccessTime = int(time.time())
        return IterableUserDict.__setitem__(self, product_id, session_data)

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


class Session:
    """See zope.app.session.interfaces.ISession"""
    implements(ISession)
    __slots__ = ('browser_id',)
    def __init__(self, request):
        self.browser_id = str(IBrowserId(request))

    def __getitem__(self, product_id):
        """See zope.app.session.interfaces.ISession"""

        # First locate the ISessionDataContainer by looking up
        # the named Utility, and falling back to the unnamed one.
        try:
            sdc = getUtility(ISessionDataContainer, product_id)
        except ComponentLookupError:
            warnings.warn(
                    'Unable to find ISessionDataContainer named %s. '
                    'Using default' % repr(product_id),
                    RuntimeWarning
                    )
            sdc = getUtility(ISessionDataContainer)

        # The ISessionDataContainer contains two levels:
        # ISessionDataContainer[product_id] == ISessionProductData
        # ISessionDataContainer[product_id][browser_id] == ISessionData
        try:
            spd = sdc[product_id]
        except KeyError:
            sdc[product_id] = SessionProductData()
            spd = sdc[product_id]

        try:
            return spd[self.browser_id]
        except KeyError:
            spd[self.browser_id] = SessionData()
            return spd[self.browser_id]


class SessionProductData(Persistent, IterableUserDict):
    """See zope.app.session.interfaces.ISessionProductData"""
    implements(ISessionProductData)
    lastAccessTime = 0
    def __init__(self):
        self.data = OOBTree()


class SessionData(Persistent, IterableUserDict):
    """See zope.app.session.interfaces.ISessionData"""
    implements(ISessionData)
    def __init__(self):
        self.data = OOBTree()

