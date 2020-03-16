Topology Release
================

How to make a Topology release?

#. Edit version::

    nano .cookiecutter.json lib/topology/__init__.py

#. Update changelog in README.rst::

    git log
    nano README.rst

#. Commit, tag::

    git commit -a
        chg: dev: Bumping version number to x.y.z.
    git tag x.y.z

#. Build wheel package::

    tox -e build

#. Push new revision and tag::

    git push
    git push origin x.y.z

#. Upload to PyPI::

    twine upload --username hpe-networking dist/topology-x.y.z.tar.gz
    twine upload --username hpe-networking dist/topology-x.y.z-py3-none-any.whl

#. Add entry in GitHub releases:

   https://github.com/HPENetworking/topology/releases
