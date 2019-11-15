.. toctree::

.. highlight:: sh

===============
Developer Guide
===============


Setup Development Environment
=============================

#. Install ``pip3`` and ``tox``:

   ::

      sudo apt-get install python3-pip
      sudo pip3 install tox

#. Configure git pre-commit hook:

   ::

      sudo pip3 install flake8 pep8-naming
      flake8 --install-hook
      git config flake8.strict true


Building Documentation
======================

::

   tox -e doc

Output will be available at ``.tox/doc/tmp/html``. It is recommended to install
the ``webdev`` package:

::

   sudo pip install webdev

So a development web server can serve any location like this:

::

   $ webdev .tox/doc/tmp/html


Running Test Suite
==================

::

   tox -e test
