
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


import socket, select, ssl, uuid, os, tempfile
from subprocess import Popen, PIPE
from os.path import join as joinpath
from os.path import abspath

# for reference: https://docs.python.org/2/library/ssl.html


class ClientConnection(object):
    """
    Used by SlockyServer to represent a client connection.
    """
    def __init__(self, ssl_socket, address):
        self.addr = address
        self.sock = ssl_socket
        self.pending = ""

    def cycle(self):
        """
        Read new data from the client, and do any processing if
        necessary.
        """
        self.pending += self.sock.read()
        #fixme process off offsets etc
        


class SlockyServer(object):
    """
    """
    def __init__(self, host, port, server_dir):
        self.__certfile = abspath(joinpath(server_dir, "certfile"))
        self.__keyfile = abspath(joinpath(server_dir, "keyfile"))
       
        try:
            assert os.path.isfile(self.__certfile)
            assert os.path.isfile(self.__keyfile)
        except AssertionError:
            self.__cert_setup(server_dir)

        self.__socket_setup(host, port)
        
    def __cert_setup(self, server_dir):
        """
        Generate new certificates etc for slocky to use.
        """

        # hokay, what follows isn't going to work; I should generate
        #
        # the key first like so:
        # - https://www.openssl.org/docs/HOWTO/keys.txt
        #
        # and then generate the cert stuff like so:
        # - https://www.openssl.org/docs/HOWTO/certificates.txt
        #

        assert os.path.isdir(server_dir)
        cmd = "openssl req -x509 -newkey rsa:4096 -keyout {0}"
        cmd += " -out {1} -days 365 -passout pass:{2}"

        tmp_file = tempfile.mkstemp()[1]

        passwd = str(uuid.uuid4())
        args = cmd.format(
            tmp_file, self.__certfile, passwd).split(" ")

        # generate an ssl cert and key
        proc = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        proc.communicate("\n"*7) # HACK, pass 7 returns to use defaults

        # generate a passwordless key
        args = "openssl pkey -in {0} -out {1} -passin pass:{2}".format(
                tmp_file, self.__keyfile, passwd).split(" ")
        print args
        proc = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        proc.communicate()

        # delete the passworded key
        os.remove(tmp_file)
        
    def __socket_setup(self, host, port):
        """
        Open and listen to our socket 
        """
        
        self.__s = socket.socket()
        self.__s.bind((host, port))
        self.__s.listen(5)
        self.__s.setblocking(0)
        self.__sockets = []
        self.__clients = []

    def __connect_client(self, socket, address):

        connect = ssl.wrap_socket(
            socket, server_side=True,
            certfile = self.__certfile,
            keyfile = self.__keyfile,
            ssl_version = ssl.PROTOCOL_TLSv1)
        client = ClientConnection(connection, addr)
        self.__sockets.append(socket)
        self.__clients.append(client)


    def process_events(self):
        """
        Schedule this somewhere, to process incoming events.
        """

        # readable, writeable, errored
        read_list = [self.__s] + self.__sockets
        # select.select used to determine which sockets actually have
        # readable data on them.  This is used to avoid making
        # non-blocking calls.
        for s in select.select(read_list, [], [], 0)[0]:
            if s is self.__s:
                # make note of any incoming connections
                self.__connect_client(*self.__s.accept())
                print "Connected from {0}".format(client.addr)
            else:
                # process data from client connection
                client = self.__clients[self.__sockets.index(s)]
                client.cycle()
                print "New data from {0}: {1}".format(
                    client.addr, client.pending)
        

    def on_message(self, msg_object):
        """
        Duckpunch me lol.
        """
        pass
    
    def send_message(self, msg_object, target=None):
        pass


def test_server():
    srv = SlockyServer('localhost', 14900, ".")
    while True:
        srv.process_events()


def test_client():
    s = socket.socket()
    ssl_sock = ssl.wrap_socket(s, ca_certs="certfile", cert_reqs=ssl.CERT_REQUIRED)
    ssl_sock.connect(('localhost', 14900))
