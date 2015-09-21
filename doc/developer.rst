.. toctree::

.. highlight:: sh

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

   1. Install mininet

   Read installation instructions on the `mininet page
   <http://mininet.org/download/#option-2-native-installation-from-source>`_

   ::

      git clone git://github.com/mininet/mininet

      cd mininet
      git checkout -b 2.2.1 2.2.1
      cd ..

      mininet/util/install.sh -a

   2. Install other requirements

   ::

      cd topology
      pip install -r requirements.txt
      pip install -r requirements.dev.txt
      pip setup.py develop

   3. If using virtualenv, also install:

   ::

      pip install -e git+git://github.com/mininet/mininet@2.2.1#egg=mininet


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
