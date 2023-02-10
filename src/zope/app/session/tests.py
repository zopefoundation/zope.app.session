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
"""Session tests

"""
import doctest
import unittest
from io import BytesIO

import transaction
from persistent import Persistent
from webtest import TestApp
from zope.app.publication.interfaces import IBeforeTraverseEvent
from zope.component import testing as placelesssetup
from zope.container.contained import Contained
from zope.interface import Interface
from zope.interface import implementer
from zope.pagetemplate.engine import AppPT
from zope.pagetemplate.pagetemplate import PageTemplate
from zope.publisher.browser import TestRequest
from zope.publisher.interfaces import IRequest
from zope.schema import SourceText
from zope.schema import TextLine
from zope.site.folder import Folder
from zope.site.interfaces import IRootFolder

from zope import component
from zope.app.session.http import CookieClientIdManager
# We continue to use the old imports to make sure that backwards
# compatibility holds.
from zope.app.session.interfaces import IClientId
from zope.app.session.interfaces import IClientIdManager
from zope.app.session.interfaces import ISession
from zope.app.session.interfaces import ISessionDataContainer
from zope.app.session.session import ClientId
from zope.app.session.session import PersistentSessionDataContainer
from zope.app.session.session import RAMSessionDataContainer
from zope.app.session.session import Session
from zope.app.session.testing import SessionLayer


# Previously from zope.app.zptpage


def setUp(test, session_data_container_class=RAMSessionDataContainer):
    placelesssetup.setUp()
    component.provideAdapter(ClientId, (IRequest,), IClientId)
    component.provideAdapter(Session, (IRequest,), ISession)
    component.provideUtility(CookieClientIdManager(), IClientIdManager)
    sdc = session_data_container_class()
    for product_id in ('', 'products.foo', 'products.bar', 'products.baz'):
        component.provideUtility(sdc, ISessionDataContainer, product_id)
    request = TestRequest(BytesIO())
    test.globs['request'] = request
    return request


def tearDown(test):
    placelesssetup.tearDown()


class IZPTPage(Interface):
    """ZPT Pages are a persistent implementation of Page Templates."""

    def setSource(text, content_type='text/html'):
        """Save the source of the page template.

        'text' must be Unicode.
        """

    def getSource():
        """Get the source of the page template."""

    source = SourceText(
        title="Source",
        description="The source of the page template.",
        required=True)


class IRenderZPTPage(Interface):

    content_type = TextLine(
        title=("Content Type"),
        description=("Content type of generated output"),
        default="text/html",
        required=True)

    def render(request, *args, **kw):
        """Render the page template.

        The first argument is bound to the top-level 'request'
        variable. The positional arguments are bound to the 'args'
        variable and the keyword arguments are bound to the 'options'
        variable.
        """


@implementer(IZPTPage, IRenderZPTPage)
class ZPTPage(AppPT, PageTemplate, Persistent, Contained):

    def getSource(self):
        raise NotImplementedError()

    def setSource(self, text, content_type='text/html'):
        self.pt_edit(text, content_type)

    # See zope.app.zptpage.interfaces.IZPTPage
    source = property(getSource, setSource, None,
                      """Source of the Page Template.""")

    def pt_getContext(self, instance, request, **_kw):
        # instance is a View component
        namespace = super().pt_getContext(**_kw)
        namespace['template'] = self
        namespace['request'] = request
        namespace['container'] = namespace['context'] = instance
        return namespace

    def pt_getEngineContext(self, namespace):
        context = self.pt_getEngine().getContext(namespace)
        context.evaluateInlineCode = self.evaluateInlineCode
        return context

    def render(self, request, *args, **keywords):
        instance = self.__parent__

        namespace = self.pt_getContext(instance, request, *args, **keywords)
        return self.pt_render(
            namespace,
            showtal=request.debug.showTAL,
            sourceAnnotations=request.debug.sourceAnnotations)


class ZPTPageEval:

    context = None
    request = None

    def index(self, **kw):
        """Call a Page Template"""

        template = self.context
        request = self.request

        request.response.setHeader('content-type',
                                   template.content_type)

        return template.render(request, **kw)


class BrowserTestCase(unittest.TestCase):

    layer = SessionLayer

    last_response = None

    def setUp(self):
        super().setUp()

        self._testapp = TestApp(self.layer.make_wsgi_app())

    def commit(self):
        transaction.commit()

    def getRootFolder(self):
        return self.layer.getRootFolder()

    def publish(self, path, headers=None, env=None):
        env = env or {}
        env['wsgi.handleErrors'] = False

        response = self._testapp.get(path, extra_environ=env, headers=headers)

        response.getBody = lambda: response.unicode_normal_body
        response.getStatus = lambda: response.status_int
        response.getHeader = lambda n: response.headers[n]
        self.last_response = response
        return response


class ZPTSessionTest(BrowserTestCase):
    content = '''
        <div tal:define="
                 session request/session:products.foo;
                 dummy python:session.__setitem__(
                        'count',
                        session.get('count', 0) + 1)
                 " tal:omit-tag="">
            <span tal:replace="session/count" />
        </div>
        '''

    layer = SessionLayer

    product_ids = ('', 'products.foo', 'products.bar', 'products.baz')

    def setUp(self):
        super().setUp()
        page = ZPTPage()
        page.source = self.content
        page.evaluateInlineCode = True
        root = self.layer.getRootFolder()
        root['page'] = page

        self.sdc = sdc = PersistentSessionDataContainer()
        for product_id in self.product_ids:
            component.provideUtility(sdc, ISessionDataContainer, product_id)

        self.commit()

    def tearDown(self):
        root = self.layer.getRootFolder()
        del root['page']
        for product_id in self.product_ids:
            component.getSiteManager().unregisterUtility(
                self.sdc, ISessionDataContainer, name=product_id)
        super().tearDown()

    def fetch(self, page='/page'):
        response = self.publish(page)
        self.assertEqual(response.getStatus(), 200)
        return response.getBody().strip()

    def test(self):
        response1 = self.fetch()
        self.assertEqual(response1, '1')
        response2 = self.fetch()
        self.assertEqual(response2, '2')
        response3 = self.fetch()
        self.assertEqual(response3, '3')


class VirtualHostSessionTest(BrowserTestCase):
    layer = SessionLayer

    def setUp(self):
        super().setUp()
        page = ZPTPage()
        page.source = '<div>Foo</div>'
        page.evaluateInlineCode = True
        root = self.getRootFolder()
        root['folder'] = Folder()
        root['folder']['page'] = page
        self.commit()

        component.provideHandler(
            self.accessSessionOnRootTraverse,
            (IBeforeTraverseEvent,))

    def tearDown(self):
        component.getGlobalSiteManager().unregisterHandler(
            self.accessSessionOnRootTraverse, (IBeforeTraverseEvent,))
        super().tearDown()

    def accessSessionOnRootTraverse(self, event):
        if IRootFolder.providedBy(event.object):
            ISession(event.request)

    def assertCookiePath(self, path):
        cookie = self.last_response.headers['Set-Cookie']
        self.assertIn('Path=' + path, cookie)

    def testShortendPath(self):
        self.publish(
            '/++skin++Rotterdam/folder/++vh++http:localhost:80/++/page')
        self.assertCookiePath('/')

    def testLongerPath(self):
        self.publish(
            '/folder/++vh++http:localhost:80/foo/bar/++/page')
        self.assertCookiePath('/foo/bar')

    def testDifferentHostname(self):
        self.publish(
            '/folder/++vh++http:foo.bar:80/++/page')
        self.assertCookiePath('/')


def test_suite():
    return unittest.TestSuite((
        doctest.DocTestSuite(),
        doctest.DocFileSuite(
            'api.rst',
            setUp=setUp,
            tearDown=tearDown,
            optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE,
        ),
        unittest.defaultTestLoader.loadTestsFromName(__name__),
    ))
