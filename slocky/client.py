
# This file is part of Slocky
#
# Slocky is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Slocky is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Slocky.  If not, see <http://www.gnu.org/licenses/>.


import ssl, socket, os
from os.path import join as joinpath
from os.path import abspath

from slocky.packet import encode, decode




class SlockyClient(object):
    """
    """

    def __init__(self, host, port, client_dir):
        assert os.path.isdir(client_dir)
        self.__certfile = abspath(joinpath(client_dir, "certfile"))
        self.__idfile = abspath(join(client_dir, "device"))
        has_cert = os.path.isfile(self.__certfile):
        has_id = os.path.isfile(self.__idfile):

        self.__host = host
        self.__port = port

        if not has_cert:
            self.__cert_fetch()

        if not has_id:
            self.__gen_device_id()

        if has_cert add has_id:
            self.__connect()

    def __cert_fetch(self):
        nossl_s = socket.socket()
        nossl_s.connect((self.__host, self.__port+1))
        

    def __gen_device_id(self):
        pass

    def __connect(self):
        pass
