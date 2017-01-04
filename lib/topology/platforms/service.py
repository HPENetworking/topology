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
topology service objects module.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from logging import getLogger


log = getLogger()


class BaseService(object):
    """
    Base class used to describe a service.

    It is mainly used to store context variables.

    :param str name: Name of the service.
    :param int port: Port of the service.
    :param str protocol: Protocol used by the service.

    :var str name: Given name in the constructor.
    :var int port: Given port in the constructor.
    :var str protocol: Given protocol in the constructor.
    :var str address: IP or FQDN of the node exposing this service. This is
     set by the engine node.
    """
    def __init__(self, name, port, protocol='tcp'):
        super(BaseService, self).__init__()
        self.name = name
        self.port = port
        self.protocol = protocol
        self.address = None

    def __str__(self):
        return '{protocol}://{address}:{port}/'.format(**self.__dict__)


__all__ = ['BaseService']
