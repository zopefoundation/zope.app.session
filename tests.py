# -*- coding: ascii -*-
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
'''
$Id$
'''
import unittest, doctest, os, os.path, sys
from zope.app import zapi
from zope.app.tests import ztapi, placelesssetup

from zope.app.session.interfaces import \
        IClientId, IClientIdManager, ISession, ISessionDataContainer, \
        ISessionPkgData, ISessionData

from zope.app.session.session import \
        ClientId, Session, \
        PersistentSessionDataContainer, RAMSessionDataContainer

from zope.app.session.http import CookieClientIdManager

from zope.publisher.interfaces import IRequest
from zope.publisher.http import HTTPRequest

from zope.pagetemplate.pagetemplate import PageTemplate

def setUp(session_data_container_class=PersistentSessionDataContainer):
    placelesssetup.setUp()
    ztapi.provideAdapter(IRequest, IClientId, ClientId)
    ztapi.provideAdapter(IRequest, ISession, Session)
    ztapi.provideUtility(IClientIdManager, CookieClientIdManager())
    sdc = session_data_container_class()
    for product_id in ('', 'products.foo', 'products.bar', 'products.baz'):
        ztapi.provideUtility(ISessionDataContainer, sdc, product_id)
    request = HTTPRequest(None, None, {}, None)
    return request

def tearDown():
    placelesssetup.tearDown()


from zope.app.appsetup.tests import TestBootstrapSubscriberBase, EventStub
class TestBootstrapInstance(TestBootstrapSubscriberBase):

    def test_bootstrapInstance(self):
        from zope.app.appsetup.bootstrap import bootstrapInstance
        bootstrapInstance(EventStub(self.db))
        from zope.app.session.bootstrap import bootstrapInstance
        bootstrapInstance(EventStub(self.db))
        from zope.app.publication.zopepublication import ZopePublication
        from zope.app.component.hooks import setSite
        from zope.app import zapi
        
        cx = self.db.open()
        root = cx.root()
        root_folder = root[ZopePublication.root_name]
        setSite(root_folder)

        zapi.getUtility(IClientIdManager)
        zapi.getUtility(ISessionDataContainer)
        
        
        cx.close()

# Test the code in our API documentation is correct
def test_documentation():
    pass
test_documentation.__doc__ = '''
    >>> request = setUp(RAMSessionDataContainer)

    %s

    >>> tearDown()

    ''' % (open(os.path.join(os.path.dirname(__file__), 'api.txt')).read(),)

def test_suite():
    return unittest.TestSuite((
        doctest.DocTestSuite(),
        doctest.DocTestSuite('zope.app.session.session'),
        doctest.DocTestSuite('zope.app.session.http'),
        unittest.makeSuite(TestBootstrapInstance),
        ))

if __name__ == '__main__':
    unittest.main()

# vim: set filetype=python ts=4 sw=4 et si

