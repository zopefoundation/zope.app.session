##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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

from zope.app.appsetup.bootstrap import BootstrapSubscriberBase


from zope.app.session.interfaces import \
     IClientIdManager, ISessionDataContainer
from zope.app.session.http import CookieClientIdManager
from zope.app.session.session import PersistentSessionDataContainer

class BootstrapInstance(BootstrapSubscriberBase):

    def doSetup(self):
        self.ensureUtility(
                IClientIdManager, 'CookieClientIdManager',
                CookieClientIdManager,
                )
        self.ensureUtility(
                ISessionDataContainer, 'PersistentSessionDataContainer',
                PersistentSessionDataContainer,
                )

bootstrapInstance = BootstrapInstance()
