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
Common utilities for communication libraries.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division


def stateprovider(stateclass, statename=None, initfunc=None):
    """
    Decorator to inject a library state into an enode.

    :param class stateclass: Class that will hold all the state / attribute of
     the library functions.
    :param str statename: Attribute name to save the instance of the state
     class in the engine node (enode). By default, the name of the state class
     is used like ``_lib_state_<stateclass>`` in lower case.
    :param function initfunc: A function to create the instance the state
     class. It receives as arguments the enode and the state class and MUST
     return and instance of that class already initialized. If ``None``, the
     default, this decorator will create an instance of the state class without
     any arguments or keyword arguments.

    Basic usage:

    ::

       from topology.libraries.utils import stateprovider

       class MyState(object):
           def __init__(self):
               self.my_variable_one = 100

       stateprovider(MyState)
       def my_library_function(enode, state, arg1, arg2, keyword_arg1=None):
           print(state.my_variable_one)
           state.my_variable_one += 100

        __all__ = ['my_library_function']

    In the above example the variable ``my_variable_one`` will be bound to the
    ``enode`` calling the library functions, and each call of that library
    function will increase it's value by 100.
    """

    # Set a default statename
    if statename is None:
        statename = '_lib_state_{}'.format(stateclass.__name__.lower())

    def decorator(func):
        def replacement(enode, *args, **kwargs):

            state = getattr(enode, statename, None)

            # Create an instance of the state class
            if state is None:

                if initfunc is not None:
                    state = initfunc(enode, stateclass)
                else:
                    state = stateclass()

                setattr(enode, statename, state)

            return func(enode, state, *args, **kwargs)

        replacement.__name__ = func.__name__
        replacement.__doc__ = func.__doc__

        return replacement
    return decorator


__all__ = ['stateprovider']
