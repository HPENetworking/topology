.. toctree::

.. highlight:: sh

===============
Developer Guide
===============


Setup Development Environment
=============================

#. Install ``pip3`` and ``tox``:

   ::

      wget https://bootstrap.pypa.io/get-pip.py
      sudo python3 get-pip.py
      sudo pip3 install tox

#. Install Graphviz for topology auto-plotting:

   ::

      sudo apt-get install graphviz

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

   sudo pip3 install webdev

So a development web server can serve any location like this:

::

   $ webdev .tox/doc/tmp/html


Running Test Suite
==================

::

   tox -e py27,py34


Running Coverage
================

::

   tox -e coverage
   webdev .tox/coverage/tmp/htmlcov/
