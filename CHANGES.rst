=========
 CHANGES
=========

6.0 (2025-09-12)
================

- Replace ``pkg_resources`` namespace with PEP 420 native namespace.


5.1 (2025-09-04)
================

- Add support for Python 3.12, 3.13.

- Drop support for Python 3.7, 3.8.


5.0 (2023-02-10)
================

- Drop support for Python 2.7, 3.5, 3.6.

- Add support for Python 3.8, 3.9, 3.10, 3.11.


4.1.0 (2018-10-22)
==================

- Add support for Python 3.7.


4.0.0 (2017-05-29)
==================

- Add support for Python 3.4, 3.5, 3.6 and PyPy.

- Remove dependency on ``ZODB3`` and other packages that are not used
  by this package, leaving behind only ``zope.session``. Packages that
  are used during testing are now test dependencies.


3.6.2 (2010-09-01)
==================

- Remove undeclared dependency on ``zope.deferredimport``.

3.6.1 (2010-02-06)
==================

- Include meta.zcml from zope.securitypolicy

3.6.0 (2009-02-01)
==================

- Use ``zope.site`` instead of ``zope.app.folder`` in tests.

3.5.2 (2009-01-27)
==================

- Fixed tearDown-Error in tests.

3.5.1 (2007-10-31)
==================

- Resolve ``ZopeSecurityPolicy`` deprecation warning.

3.5.0 (2007-09-27)
==================

* A release to override an untagged, unreasoned dev release in
  ``download.zope.org/distribution``.


3.4.3 (2007-09-27)
==================

* Fix package meta-data.

3.4.2 (2007-09-24)
==================

- rebumped to replace faulty egg

- added missing dependecy to ``zope.session``


3.4.1 (2007-09-24)
==================

- Added missing files to egg distribution


3.4.0 (2007-09-24)
==================

- Initial documented release
