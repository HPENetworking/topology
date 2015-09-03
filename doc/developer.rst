.. toctree::

===============
Developer Guide
===============


Setup Development Environment
=============================

#. Install `pip` and `virtualenv`:

   ::

      sudo apt-get install python-pip
      sudo pip install virtualenv

#. Create a virtual environment:

   ::

      virtualenv topology_env
      source topology_env/bin/activate

#. Install application requirements and development requirements:

   ::

      cd topology
      pip install -r requirements.txt
      pip install -r requirements.dev.txt
      pip setup.py develop

#. Configure git pre-commit hook:

   ::

      flake8 --install-hook
      git config flake8.strict true

.. note::

   To exit the virtual environment issue the `deactivate` command.


Building Documentation
======================

::

   tox -e doc

Output will be available at `.tox/doc/tmp/html`. It is recommended to install
the `webdev` package:

::

   sudo pip install webdev

So a development web server can serve any location like this:

::

   $ webdev .tox/doc/tmp/html


Running Test Suite
==================

::

   tox -e py27,py34
