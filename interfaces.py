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
"""Interfaces for session service.

$Id: interfaces.py,v 1.1 2004/03/10 12:11:19 srichter Exp $
"""
import re
from zope.interface import Interface
from zope.interface.common.mapping import IMapping, IReadMapping, IWriteMapping
from zope import schema
from zope.app.container.interfaces import IContainer
from zope.app.i18n import ZopeMessageIDFactory as _


class IBrowserIdManager(Interface):
    """Manages sessions - fake state over multiple browser requests."""

    def getBrowserId(request):
        """Return the IBrowserId for the given request.
        
        If the request doesn't have an attached sessionId a new one will be
        generated.

        This will do whatever is possible to do the HTTP request to ensure the
        session id will be preserved. Depending on the specific method,
        further action might be necessary on the part of the user.  See the
        documentation for the specific implementation and its interfaces.
        """


    """ XXX: Want this
    def invalidate(browser_id):
        ''' Expire the browser_id, and remove any matching ISessionData data 
        '''
    """


class ICookieBrowserIdManager(IBrowserIdManager):
    """Manages sessions using a cookie"""

    namespace = schema.TextLine(
            title=_('Cookie Name'),
            description=_(
                "Name of cookie used to maintain state. "
                "Must be unique to the site domain name, and only contain "
                "ASCII letters, digits and '_'"
                ),
            required=True,
            min_length=1,
            max_length=30,
            constraint=re.compile("^[\d\w_]+$").search,
            )

    cookieLifetime = schema.Int(
            title=_('Cookie Lifetime'),
            description=_(
                "Number of seconds until the browser expires the cookie. "
                "Leave blank expire the cookie when the browser is quit. "
                "Set to 0 to never expire. "
                ),
            min=0,
            required=False,
            default=None,
            missing_value=None,
            )


class IBrowserId(Interface):
    """A unique ID representing a session"""

    def __str__():
        """As a unique ASCII string"""


class ISessionDataContainer(IReadMapping, IWriteMapping):
    """Stores data objects for sessions.

    The object implementing this interface is responsible for expiring data as
    it feels appropriate.

    Used like::

      session_data_container[browser_id][product_id][key] = value

    Attempting to access a key that does not exist will raise a KeyError.
    """

    timeout = schema.Int(
            title=_(u"Timeout"),
            description=_(
                "Number of seconds before data becomes stale and may "
                "be removed"),
            default=3600,
            required=True,
            min=1,
            )
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


class ISession(IMapping):
    """A session object that keeps the state of the user.

    To access bits of data within an ISessionDataContainer, we
    need to know the browser_id, the product_id, and the actual key.
    An ISession is a wrapper around an ISessionDataContainer that
    simplifies this by storing the browser_id and product_id enabling
    access using just the key.
    """

    def __init__(session_data_container, browser_id, product_id):
        """Construct an ISession"""

