# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2020 Hewlett Packard Enterprise Development LP
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
Logging module for the Topology Modular Framework.
"""

import logging
from abc import ABCMeta
from os.path import join
from inspect import stack
from collections import OrderedDict
from distutils.dir_util import mkpath
from weakref import WeakValueDictionary
from datetime import datetime

from six import add_metaclass


LEVELS = OrderedDict([
    ('NOTSET', logging.NOTSET),
    ('DEBUG', logging.DEBUG),
    ('INFO', logging.INFO),
    ('WARNING', logging.WARNING),
    ('ERROR', logging.ERROR),
    ('CRITICAL', logging.CRITICAL),
])
"""Simple map with the default logging levels."""


class PexpectFileHandler(logging.FileHandler):
    """
    A handler class which writes formatted logging records to disk
    files.  Works like FileHandler from the std, but doesn't emit line
    changes after records, maintaining a shape that is closer to the actual
    PTTY's stream pexpect uses.
    """

    def emit(self, record):
        """
        Emit a record.
        If the stream was not opened because 'delay' was specified in the
        constructor, emitting the actual record.
        """
        if self.stream is None:
            self.stream = self._open()
        try:
            msg = self.format(record)
            stream = self.stream
            stream.write(msg)
            self.flush()
        except Exception:
            self.handleError(record)


@add_metaclass(ABCMeta)
class BaseLogger(object):
    """
    Base class for Topology logger classes.

    :param OrderedDict nameparts: Namespaced name of the logger.
    :param bool propagate: Propagate messages to the root logger.
    :param int level: Logging level as in Python's logging framework.
     .. autodata:: topology.logging.LEVELS
    :param str log_dir: Directory to store the logging file
     (if any, see subclasses).

    Object read-only properties:

    :var OrderedDict nameparts: Namespaced name of the logger.
     For example::

         OrderedDict([
             'context': 'test_bar',
             'category': 'core',
             'name': 'mylogger'
         ])

    :var str name: Name of this logger as concatenated nameparts.
     For example:

         test_bar.core.mylogger

    Object read-write properties:

    :var bool propagate: True if message propagation to the root logger is
     enabled.
    :var int level: Current logging level for this logger.
    :var log_dir: Current logging directory for this logger.
    """

    def __init__(
        self, nameparts,
        propagate=False,
        level=logging.NOTSET,
        log_dir=None,
        *args, **kwargs
    ):
        super(BaseLogger, self).__init__()
        self._nameparts = nameparts
        self._propagate = None
        self._level = None
        self._log_dir = None

        self._name = ''.join(map(str, nameparts.values()))
        self.logger = logging.getLogger(self._name)

        self.propagate = propagate
        self.level = level
        self.log_dir = log_dir

    @property
    def nameparts(self):
        return OrderedDict(self._nameparts)

    @property
    def name(self):
        return self._name

    @property
    def propagate(self):
        return self._propagate

    @propagate.setter
    def propagate(self, propagate):
        self.logger.propagate = propagate

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, level):
        self._level = level
        self.logger.setLevel(self._level)

    @property
    def log_dir(self):
        return self._log_dir

    @log_dir.setter
    def log_dir(self, log_dir):
        self._log_dir = log_dir


@add_metaclass(ABCMeta)
class StdOutLogger(BaseLogger):
    """
    Logger that logs to the standard output.
    """

    def __init__(self, *args, **kwargs):
        super(StdOutLogger, self).__init__(*args, **kwargs)

        self.logger.addHandler(logging.StreamHandler())

    def log(self, message):
        """
        Log a message to standard output.

        :param str message: Message to log.
        """
        self.logger.log(self._level, message)


@add_metaclass(ABCMeta)
class FileLogger(BaseLogger):
    """
    Subclass of BaseLogger that adds a PexpectFileHandler.

    This class implements additional logic for when the ``log_dir`` path is
    changed. It will create a file with the name of the logger under the
    ``log_dir`` with the ``.log`` extension.

    :param str file_formatter: Format to use in the PexpectFileHandler,
     defaulting to ``logging.BASIC_FORMAT``.
    """

    def __init__(self, *args, **kwargs):
        self._file_handler = None
        self._file_formatter = kwargs.pop(
            'file_formatter', logging.BASIC_FORMAT
        )
        super(FileLogger, self).__init__(*args, **kwargs)

    @BaseLogger.log_dir.setter
    def log_dir(self, log_dir):

        # Do not recreate a new file handler if nothing has changed
        if log_dir == self._log_dir:
            return

        def reset_file_handler():
            self.logger.removeHandler(self._file_handler)
            self._file_handler.close()
            self._file_handler = None

        if log_dir:

            # Remove old file handler
            if self._file_handler:
                reset_file_handler()

            # Create file handler
            fh = PexpectFileHandler(
                join(log_dir, '{}.{}'.format(self._name, 'log'))
            )

            # Create formatter
            formatter = logging.Formatter(self._file_formatter)
            fh.setFormatter(formatter)

            # Register handler
            self.logger.addHandler(fh)
            self._file_handler = fh

        elif self._file_handler:
            reset_file_handler()

        self._log_dir = log_dir


class PexpectLogger(FileLogger):
    """
    Special subclass that implements a logger to be used with Pexpect
    ``logfile`` keyword argument.

    **Purpose:** to log every character in the pexpect session.

    Pexpect ``logfile`` is expected to be an open file-like object, so this
    class implements the ``write()`` and ``flush()`` operations for effective
    duck-typing.

    To implement one logging per ``flush()`` this class implements a local
    buffer.

    Pexpect loggers can be located with the name::

        <context>.pexpect.<node_identifier>.<shell_name>.<connection>

    Where ``<context>`` is optional if running interactively or if the context
    in the LoggerManager has not been set.

    :param str encoding: Encoding to log into. The ``write()`` interface expect
     bytes, so in order to log in plain text it is required to perform a
     decoding. Defaults to ``utf-8``.
    :param str errors: Handling of decoding errors. The ``write()`` interface
     may find undecodeable characters when decoding with the selected encoding,
     so the handling of errors needs to be defined. The values available are
     the same ones that the ``decode`` method of a bytes object expects in its
     ``error`` keyword argument. Defaults to ``ignore``.
    """

    _pexpect_loggers = {}

    def __new__(cls, *args, **kwargs):
        name = ''.join(map(str, args[0].values()))

        if name not in cls._pexpect_loggers.keys():
            cls._pexpect_loggers[name] = {
                'logger': object.__new__(cls), 'initialized': False
            }

        return cls._pexpect_loggers[name]['logger']

    def __init__(self, *args, **kwargs):
        name = ''.join(map(str, args[0].values()))

        # This is done to prevent a second call to getLogger in
        # BaseLogger.__init__ since a second call will add anothe handle to the
        # logger object, introducing duplicate records in the log file.
        if self._pexpect_loggers[name]['initialized']:
            return

        self._encoding = kwargs.pop('encoding', 'utf-8')
        self._errors = kwargs.pop('errors', 'ignore')
        self._buffer = []

        if 'file_formatter' not in kwargs:
            kwargs['file_formatter'] = '%(message)s'

        self._pexpect_loggers[name]['initialized'] = True

        super(PexpectLogger, self).__init__(*args, **kwargs)

    def write(self, data):
        self._buffer.append(
            data.decode(encoding=self._encoding, errors=self._errors)
        )

    def flush(self):
        data = ''.join(self._buffer)
        del self._buffer[:]
        self.logger.log(self._level, data)


class PexpectLoggerGeneric(object):
    def __init__(self, *args, **kwargs):
        args[0]['category'] = 'pexpect'
        self._pexpect_logger = PexpectLogger(*args, **kwargs)

    def __getattr__(self, name):
        def inner(*args, **kwargs):
            getattr(self._pexpect_logger, name)(*args, **kwargs)
        return inner


class PexpectLoggerRead(PexpectLoggerGeneric):
    pass


class PexpectLoggerSend(PexpectLoggerGeneric):
    def write(self, data):
        self._pexpect_logger._buffer.append(
            '\n\n{} '.format(datetime.now().isoformat())
        )
        self._pexpect_logger.write(data)
        self._pexpect_logger.write(b'\n')


class ConnectionLogger(BaseLogger):
    """
    Logger for shell connections.

    **Purpose:** to log every ``send_command`` and ``get_response`` in a
    low-level connection.

    Connection loggers can be located with the name::

        <context>.pexpect.<node_identifier>.<shell_name>.<connection>

    Where ``<context>`` is optional if running interactively or if the context
    in the LoggerManager has not been set.
    """

    def __init__(self, *args, **kwargs):
        super(ConnectionLogger, self).__init__(*args, **kwargs)
        self.logger.addHandler(logging.StreamHandler())

    def log_send_command(self, command, matches, newline, timeout):
        fields = {
            'command': command,
            'matches': matches,
            'newline': newline,
            'timeout': timeout
        }
        fields.update(self._nameparts)

        log_entry = (
            '[{node_identifier}].get_shell({shell_name}).send_command('
            '\'{command}\', '
            'matches={matches}, newline={newline}, timeout={timeout}'
            ')'
        ).format(**fields)
        self.logger.info(log_entry)

    def log_get_response(self, response):
        fields = {
            'response': response
        }
        fields.update(self._nameparts)

        log_entry = (
            '[{node_identifier}].get_shell({shell_name}).get_response() '
            '->\n'
            '{response}'
        ).format(**fields)
        self.logger.info(log_entry)


class StepLogger(StdOutLogger):
    """
    Stepper logging class.

    This class will log a message and will show the step number and the caller
    name and line number.
    """

    def __init__(
        self, nameparts=OrderedDict(
            [('test_suite', ''), ('test_case', '')]
        ), *args, **kwargs
    ):

        self.step = 0

        for part in ['test_suite', 'test_case']:
            if part not in nameparts:
                raise RuntimeError(
                    'Badly named StepLogger. Missing the {} '
                    'name part: {}'.format(part, nameparts)
                )
            setattr(self, '_{}'.format(part), nameparts[part])

        super(StepLogger, self).__init__(nameparts, *args, **kwargs)

    def __call__(self, msg):
        # Update step count
        self.step += 1

        # Fetch information of the caller
        (
            frame, filename, line_number,
            function_name, lines, index
        ) = stack()[1]

        # Determine execution context
        execution_context = self._test_case
        if function_name != self._test_case:
            execution_context = '{}->{}'.format(
                execution_context,
                function_name
            )
        execution_context = '{}.{}'.format(
            self._test_suite, execution_context
        )

        # Log message
        self.log(
            '>>> [{:03d}] :: {}:{}\n{}'.format(
                self.step, execution_context, line_number,
                '\n'.join(
                    [
                        '... {}'.format(line)
                        for line in msg.strip().splitlines()
                    ]
                )
            )
        )


class LoggingManager(object):
    """
    Defines an object that manage and create loggers for Topology components.

    Only an instance of this class is to be created, this instance exists in
    this module and is to be used by other components by importing its
    ``get_logger`` method straigth from this module.

    This method will return a logger tailored for each of these categories,
    if those loggers are implemented:

    #. core
    #. library
    #. platform
    #. user
    #. node
    #. shell
    #. connection
    #. pexpect
    #. service
    #. step

    Read-only properties:

    :var categories: A list of available logging categories.

    Read-write properties:

    :var str logging_directory: Framework wide logging directory. Any change on
     this setting will be notified to all loggers.
    :var str logging_context: Current framework wide logging context.
    """

    def __init__(self, default_level=logging.INFO, default_propagate=False):
        super(LoggingManager, self).__init__()
        """
        Framework logging manager.
        """
        self._log_dir = None
        self._log_context = None

        self._categories = OrderedDict([
            # module
            ('core', None),
            # name
            ('library', None),
            # name
            ('platform', None),
            # test case
            ('user', None),
            # node identifier
            ('node', None),
            # node identifier, shell name
            ('shell', None),
            # node identifier, shell name, connection
            ('connection', ConnectionLogger),
            # node identifier, shell name, connection
            ('pexpect', PexpectLogger),
            # node identifier, shell name, connection
            ('pexpect_read', PexpectLoggerRead),
            # node identifier, shell name, connection
            ('pexpect_send', PexpectLoggerSend),
            # node identifier, service name, port
            ('service', None),
            # step
            ('step', StepLogger)
        ])
        self._loggers = {
            key: WeakValueDictionary() for key in self._categories.keys()
        }

        self._default_level = default_level
        self._levels = {
            key: self._default_level for key in self._categories.keys()
        }

        self._default_propagate = default_propagate
        self._propagate = {
            key: self._default_propagate for key in self._categories.keys()
        }

    @property
    def categories(self):
        return list(self._categories.keys())

    @property
    def logging_directory(self):
        return self._log_dir

    @logging_directory.setter
    def logging_directory(self, log_dir):
        mkpath(log_dir)
        self._log_dir = log_dir

        # Notify all categories of a log directory change
        for category in self._loggers.values():
            for logger in category.values():
                logger.log_dir = log_dir

    @property
    def logging_context(self):
        return self._log_context

    @logging_context.setter
    def logging_context(self, log_context):
        self._log_context = log_context

        # XXX: The logging context is built-in in the logger name.
        #      By design (?), once a logger was created for a given context,
        #      it cannot change.

    def set_category_level(self, category, level):
        """
        Set the logging level property to all logger in the given category.

        :param str category: Name of the category.
        :param int level: Value to set the level property.
        """
        if category not in self._categories.keys():
            raise ValueError(
                'Unknown category "{}"'.format(category)
            )
        self._levels[category] = level
        for logger in self._loggers[category].values():
            logger.level = level

    def set_category_propagate(self, category, propagate):
        """
        Set the propagate property to all logger in the given category.

        :param str category: Name of the category.
        :param bool propagate: Value of set the propagate property.
        """
        if category not in self._categories.keys():
            raise ValueError(
                'Unknown category "{}"'.format(category)
            )
        self._propagate[category] = propagate
        for logger in self._loggers[category].values():
            logger.propagate = propagate

    def get_logger(self, name, category='core', *args, **kwargs):
        """
        Get a logger tailored for the given category.

        :param name: Full namespaced name or simple name.
        :type name: OrderedDict or str
        :param str category: Category of the logger.

        :return: A new logger instance of the given category.
        :rtype: BaseLogger
        """
        if category not in self._categories.keys():
            raise ValueError(
                'Unknown category "{}" for logger {}'.format(category, name)
            )

        # Prepend context and category to the nameparts namespace specifier
        nameparts = OrderedDict()
        if self._log_context is not None:
            nameparts['log_context'] = self._log_context
        nameparts['category'] = category

        if isinstance(name, OrderedDict):
            nameparts.update(name)
        else:
            nameparts['name'] = name

        clss = self._categories[category]
        if clss is not None:

            # Instance logger
            instance = clss(
                nameparts,
                propagate=self._propagate[category],
                level=self._levels[category],
                log_dir=self._log_dir,
                *args, **kwargs
            )

            # Append logger to category registry
            self._loggers[category][id(instance)] = instance
            return instance

        raise NotImplementedError(
            'Category "{}" not implemented'.format(category)
        )


manager = LoggingManager()
"""
Main framework wide instance of :py:class:`LoggingManager`.
"""

get_logger = manager.get_logger


__all__ = [
    'manager',
    'get_logger'
]

__api__ = [
    'LEVELS',
    'BaseLogger',
    'FileLogger',
    'PexpectLogger',
    'PexpectLoggerRead',
    'PexpectLoggerSend',
    'ConnectionLogger',
    'LoggingManager'
] + __all__
