# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
topology module for interactive mode.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging
from atexit import register
from inspect import ismodule
from traceback import format_exc
from os.path import join, expanduser, isfile


log = logging.getLogger(__name__)


def catch_exc(func):
    """
    Decorator for in-shell exception handling.

    This is particularly required for ``readline`` hooks, as they run in the
    C library and cannot catch any Python exception ocurring in them.
    """
    def catcher(*args):
        try:
            return func(*args)
        except Exception:
            log.error(format_exc())
    return catcher


class NamespaceCompleter(object):
    """
    Readline completer using a dictionary namespace.
    """

    def __init__(self, ns):
        super(NamespaceCompleter, self).__init__()
        self.matches = []
        self.ns = ns

    def search_tree(self, root, path):
        """
        Search for a node in a Python object as if it were a tree: namespaces,
        modules, objects, method, attributes, etc.

        :param root: The root Python object.
        :param list path: List of names representing the path.
        :rtype: list
        :return: The subnode or None if not found.
        """
        node = root

        for p in path:

            attrs = self.dict_attributes(node)

            if p not in attrs:
                node = None
                break

            node = attrs[p]

        return node

    def dict_attributes(self, element):
        """
        Type aware attributes to dictionary function.

        :param element: Python object to list attributes.
        :rtype: dict
        :return: A dict of the element attributes.
        """
        if element is not None:

            # Element is a dictionary, return itself
            if isinstance(element, dict):
                return element

            # Element is a module as has a __all__ defined
            if ismodule(element) and hasattr(element, '__all__'):
                return {
                    k: v for k, v in vars(element).items()
                    if k in element.__all__
                }

            # The element can be converted to dict
            if hasattr(element, '__dict__'):
                return vars(element)

        return {}

    def format_matches(self, path, attrs, prefixed):
        """
        Format a list of attributes to be shown in autocompleter.

        :param path: List of string representing the path to the node.
        :param attrs: List of attributes of the node.
        :param prefixed: Prefix attributes must have in order to be shown.
        :rtype: list
        :return: Formatted list of attributes.
        """
        # Filter super private attributes
        attrs = [a for a in attrs if not a.startswith('__')]

        # Filter attributes if a prefix is required
        if prefixed:
            attrs = [a for a in attrs if a.startswith(prefixed)]

        return ['.'.join(path + [a]) for a in attrs]

    @catch_exc
    def complete(self, text, state):

        if state == 0:  # On first trigger, build possible matches

            path = text.split('.')
            search = path.pop()

            subnode = self.search_tree(self.ns, path)
            attributes = sorted(self.dict_attributes(subnode))
            self.matches = self.format_matches(path, attributes, search)

        # Return match indexed by state
        try:
            return self.matches[state]
        except IndexError:
            return None


def interact(mgr):
    """
    Shell setup function.

    This function will setup the library, create the default namespace with
    shell symbols, setup the history file, the autocompleter and launch a shell
    session.
    """
    print('Engine nodes available for communication:')
    print('    {}'.format(', '.join(mgr.nodes.keys())))

    # Create and populate shell namespace
    ns = {
        'topology': mgr
    }
    for key, enode in mgr.nodes.items():
        ns[key] = enode

    # Configure readline, history and autocompleter
    import readline

    histfile = join(expanduser('~'), '.topology_history')
    if isfile(histfile):
        try:
            readline.read_history_file(histfile)
        except IOError:
            log.error(format_exc())
    register(readline.write_history_file, histfile)

    completer = NamespaceCompleter(ns)
    readline.set_completer(completer.complete)
    readline.parse_and_bind('tab: complete')

    # Python's Interactive
    from code import interact as pyinteract
    pyinteract('', None, ns)


__all__ = ['NamespaceCompleter', 'interact']
