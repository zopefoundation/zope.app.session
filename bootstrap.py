##############################################################################
#
# Copyright (c) 2002, 2004 Zope Corporation and Contributors.
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
"""Bootstrap code.

This module contains code to bootstrap a Zope3 instance.  For example
it makes sure a root folder exists and creates and configures some
essential services.

$Id$
"""

from zope.app.appsetup.bootstrap import ensureUtility, getInformationFromEvent

from zope.app.session.interfaces import \
     IClientIdManager, ISessionDataContainer
from zope.app.session.http import CookieClientIdManager
from zope.app.session.session import PersistentSessionDataContainer

def bootStrapSubscriber(event):
    """Subscriber to the IDataBaseOpenedEvent

    Create utility at that time if not yet present
    """

    db, connection, root, root_folder = getInformationFromEvent(event)

    ensureUtility(
        root_folder,
        IClientIdManager, 'CookieClientIdManager',
        CookieClientIdManager,
        )
    ensureUtility(
        root_folder,
        ISessionDataContainer, 'PersistentSessionDataContainer',
        PersistentSessionDataContainer,
        )

    get_transaction().commit()
    connection.close()
