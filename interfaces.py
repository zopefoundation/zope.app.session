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
"""Interfaces for session service.

$Id$
"""
import re
from zope.interface import Interface
from zope.interface.common.mapping import IMapping


class IClientIdManager(Interface):
    """Manages sessions - fake state over multiple client requests."""

    def getClientId(request):
        """Return the client id for the given request as a string.
        
        If the request doesn't have an attached sessionId a new one will be
        generated.

        This will do whatever is possible to do the HTTP request to ensure the
        session id will be preserved. Depending on the specific method,
        further action might be necessary on the part of the user.  See the
        documentation for the specific implementation and its interfaces.
        """


    """ XXX: Want this
    def invalidate(client_id):
        ''' Expire the client_id, and remove any matching ISessionData data 
        '''
    """

class IPersistentSessionDataManager(IMapping):
    """Manage IPersistentSessionData objects by client id
    """

    def __getitem__(self, client_id):
        """Returns data for a client id

        If data hasn't been stored previously, a new IPersistentSessionData
        will be created and returned.
        
        """
    
class IPersistentSessionData(IMapping):
    """Provide persistent session storage

    Data are stored persistently and transactionally. Data stored must
    be persistent or picklable.

    Note that this type of sessionstoreage should not be written to
    very frequently.
    """

    def __getitem__(self, application_id):
        """Returns data for an application id

        If data hasn't been stored previously, a new mapping object
        will be created and returned.
        
        """
