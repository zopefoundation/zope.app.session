##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Setup for zope.app.session package
"""
import os

from setuptools import setup, find_packages

def read(*rnames):
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        return f.read()

setup(name='zope.app.session',
    version='4.0.0',
    author='Zope Corporation and Contributors',
    author_email='zope-dev@zope.org',
    description='Zope session',
    long_description=(
        read('README.rst')
        + '\n\n' +
        read('src', 'zope', 'app', 'session', 'api.rst')
        + '\n\n' +
        read('CHANGES.rst')
    ),
    license='ZPL 2.1',
    keywords="zope3 session",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        'Framework :: Zope3',
    ],
    url='http://github.com/zopefoundation/zope.app.session',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['zope', 'zope.app'],
    extras_require={
        'test': [
            'transaction',
            'webtest',
            'zope.app.basicskin >= 4.0.0',
            'zope.app.form >= 5.0.0',
            'zope.app.appsetup >= 4.0.0',
            'zope.app.component >= 4.0.0',
            'zope.app.container >= 4.0.0',
            'zope.app.publication >= 4.2.1',
            'zope.app.rotterdam >= 4.0.1',
            'zope.app.securitypolicy',
            'zope.app.wsgi',
            'zope.container',
            'zope.pagetemplate',
            'zope.site',
            'zope.testbrowser',
            'zope.testing',
            'zope.testrunner',
        ],
    },
    install_requires=[
        'setuptools',
        'zope.session',
    ],
    include_package_data=True,
    zip_safe=False,
)
