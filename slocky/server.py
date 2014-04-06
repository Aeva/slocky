
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


import socket, select, ssl, uuid, os, tempfile, random, re, weakref
from subprocess import Popen, PIPE
from os.path import join as joinpath
from os.path import abspath

# for reference: https://docs.python.org/2/library/ssl.html


class ClientConnection(object):
    """
    Used by SlockyServer to represent a client connection.
    """
    def __init__(self, server, ssl_socket, address):
        self.addr = address
        self.sock = ssl_socket
        self.pending = ""
        self.__server = weakref.ref(server)

    def cycle(self):
        """
        Read new data from the client, and do any processing if
        necessary.
        """

        new_data = self.sock.read()
        if new_data:
            self.pending += new_data
            print "New data from {0}: {1}".format(self.addr, new_data)
        



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
        self.__pending_devices = []

    def __connect_client(self, socket, address):

        ssl_wrapper = ssl.wrap_socket(
            socket, server_side=True,
            certfile = self.__certfile,
            keyfile = self.__keyfile,
            ssl_version = ssl.PROTOCOL_TLSv1)
        client = ClientConnection(ssl_wrapper, address)
        self.__clients.append(client)
        return client

    def process_events(self):
        """
        Schedule this somewhere, to process incoming events.
        """

        # readable, writeable, errored
        read_list = [self.__s]
        # use select to make listening for new connections to be
        # non-blocking
        for s in select.select(read_list, [], [], 0)[0]:
            if s is self.__s:
                # make note of any incoming connections
                args = [self] + self.__s.accept()
                client = self.__connect_client(*args)
                print "Connected from {0}".format(client.addr)

        # client.sock.read() is non-blocking, so we don't need to do
        # anything fancy to see if there is new data or not in a
        # timely fashion.
        for client in self.__clients:
            client.cycle()
        
    def on_message(self, msg_object):
        """
        Duckpunch me lol.
        """
        pass
    
    def send_message(self, msg_object, target=None):
        pass

    def add_new_device(self):
        """
        Generate a pass phrase for passing the cert to a new client.
        """

        magic_words = []
        with open("/usr/share/dict/words") as dump:
            words = dump.readlines()
            random.shuffle(words)
            i = 0
            while len(magic_words) < 4:
                word = words[i].strip()
                i += 1
                if len(word) >= 4 and len(word) < 8 \
                   and word == word.lower() and not word.endswith("s")\
                   and re.match(r"[a-z]+", word):
                    magic_words.append(word)

        device_code = " ".join(magic_words)
        self.__pending_devices.append(device_code)
        return device_code
