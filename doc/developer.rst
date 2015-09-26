.. toctree::

.. highlight:: sh

===============
Developer Guide
===============


Setup Development Environment
=============================

#. Install ``pip`` and ``tox``:

   ::

      sudo apt-get install python-pip
      sudo pip install tox

#. Configure git pre-commit hook:

   ::

      sudo pip install flake8 pep8-naming
      flake8 --install-hook
      git config flake8.strict true

#. Configure your environment to run without root:

   ::

      sudo groupadd topology
      sudo usermod -a -G topology YOURUSER
      sudo sh -c 'echo "%topology ALL = (root) NOPASSWD: /sbin/ip" > /etc/sudoers.d/topology'

   Now logout and login again. Confirm your you're in the ``topology`` group
   with:

   ::

      $ id
      ...,1001(topology)

#. Download and install Docker:

   ::

      FIXME


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

   tox -e py27,py34
