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
"""Simplistic session service implemented using cookies.

This is more of a demonstration than a full implementation, but it should
work.

$Id$
"""
import sha, time, string, random, hmac, logging
from UserDict import IterableUserDict
from heapq import heapify, heappop

from persistent import Persistent
from zope.server.http.http_date import build_http_date
from zope.interface import implements
from zope.interface.common.mapping import IMapping
from zope.app import zapi
from BTrees.OOBTree import OOBTree
from zope.app.utility.interfaces import ILocalUtility
from zope.app.annotation.interfaces import IAttributeAnnotatable

from interfaces import IBrowserIdManager, IBrowserId, ICookieBrowserIdManager, \
                       ISessionDataContainer, ISession
from zope.app.container.interfaces import IContained

cookieSafeTrans = string.maketrans("+/", "-.")

def digestEncode(s):
    """Encode SHA digest for cookie."""
    return s.encode("base64")[:-2].translate(cookieSafeTrans)


class BrowserId(str):
    """A browser id"""
    implements(IBrowserId)


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
        return BrowserId(s + digestEncode(mac))

    def getRequestId(self, request):
        """Return the IBrowserId encoded in request or None if it's
        non-existent."""
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
            return BrowserId(sid)

    def setRequestId(self, request, id):
        """Set cookie with id on request."""
        # XXX Currently, the path is the ApplicationURL. This is reasonable,
        #     and will be adequate for most purposes.
        #     A better path to use would be that of the folder that contains
        #     the service-manager this service is registered within. However,
        #     that would be expensive to look up on each request, and would
        #     have to be altered to take virtual hosting into account.
        #     Seeing as this service instance has a unique namespace for its
        #     cookie, using ApplicationURL shouldn't be a problem.

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
        ''' See zope.app.interfaces.utilities.session.IBrowserIdManager '''
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

    def __getitem__(self, key):
        rv = IterableUserDict.__getitem__(self, key)
        now = time.time()
        # Only update lastAccessTime once every few minutes, rather than
        # every hit, to avoid ZODB bloat since this is being stored 
        # persistently
        if rv.lastAccessTime + self.sweepInterval < now:
            rv.lastAccessTime = now
            # XXX: When scheduler exists, this method should just schedule
            # a sweep later since we are currently busy handling a request
            # and may end up doing simultaneous sweeps
            self.sweep()
        return rv

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


class SessionData(Persistent, IterableUserDict):
    ''' Mapping nodes in the ISessionDataContainer tree '''
    implements(IMapping)

    def __init__(self):
        self.data = OOBTree()
        self.lastAccessTime = time.time()


class Session(IterableUserDict):
    implements(ISession)
    def __init__(self, data_manager, browser_id, product_id):
        ''' See zope.app.interfaces.utilities.session.ISession '''
        browser_id = str(browser_id)
        product_id = str(product_id)
        try:
            data = data_manager[browser_id]
        except KeyError:
            data_manager[browser_id] = SessionData()
            data_manager[browser_id][product_id] = SessionData()
            self.data = data_manager[browser_id][product_id]
        else:
            try:
                self.data = data[product_id]
            except KeyError:
                data[product_id] = SessionData()
                self.data = data[product_id]


def getSession(context, request, product_id, session_data_container=None):
    ''' Retrieve an ISession. session_data_container defaults to 
        an ISessionDataContainer utility registered with the name product_id

        XXX: This method will probably be changed when we have an
            Interaction or other object that combines context & request
            into a single object.
    '''
    if session_data_container is None:
        dc = zapi.getUtility(context, ISessionDataContainer, product_id)
    elif ISessionDataContainer.providedBy(session_data_container):
        dc = session_data_container
    else:
        dc = zapi.getUtility(
                context, ISessionDataContainer, session_data_container
                )

    bim = zapi.getUtility(context, IBrowserIdManager)
    browser_id = bim.getBrowserId(request)
    return Session(dc, browser_id, product_id)


