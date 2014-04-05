
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


import socket, ssl, uuid
from subprocess import Popen, PIPE
from os.path import join as joinpath
from os.path import abspath, isfile, isdir


class SlockyServer(object):
    """
    """

    def __init__(self, server_dir):
        self.__certfile = abspath(joinpath(server_dir, "certfile"))
        self.__keyfile = abspath(joinpath(server_dir, "keyfile"))
       
        try:
            assert isfile(self.__certfile)
            assert isfile(self.__keyfile)
        except AssertionError:
            self.__cert_setup(server_dir)

        
    def __cert_setup(self, server_dir):
        """
        Generate new certificates etc for slocky to use.
        """
        assert isdir(server_dir)
        cmd = "openssl req -x509 -newkey rsa:4096 -keyout {0} -out {1} -days 365 -passout pass:{2}".format(
            self.__keyfile,
            self.__certfile,
            str(uuid.uuid4()))

        proc = Popen(cmd.split(" "), stdin=PIPE, stdout=PIPE, stderr=PIPE)
        proc.communicate("\n"*7) # pass 7 returns

        import pdb; pdb.set_trace()
        

    def __socket_setup(self, server_dir):
        pass

    
    def on_message(self, msg_object):
        """Duckpunch me."""
        pass


    def send_message(self, msg_object, target=None):
        pass
