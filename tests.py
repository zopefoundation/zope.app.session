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
"""XXX short summary goes here.

$Id$
"""
import unittest
from zope.testing.doctestunit import DocTestSuite


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

        zapi.getUtility(IBrowserIdManager)
        zapi.getUtility(ISessionDataContainer)
        
        
        cx.close()


def test_suite():
    return unittest.TestSuite((
        DocTestSuite('zope.app.session.http'),
        DocTestSuite('zope.app.session.persist'),
        unittest.makeSuite(TestBootstrapInstance),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

