
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
import random, re, weakref, time, hashlib
from subprocess import Popen, PIPE
from os.path import join as joinpath
from os.path import abspath

from slocky.packet import encode, decode
from slocky.words import BASIC_ENGLISH

# for reference: https://docs.python.org/2/library/ssl.html


class ClientConnection(object):
    """
    Used by SlockyServer to represent a client connection.
    """
    def __init__(self, server, ssl_socket, address):
        self.addr = address
        self.sock = ssl_socket
        self.sock.setblocking(0)
        self.pending = ""
        self._server = weakref.ref(server)
        self.device_id = None

    def assign_device_id(self):
        """
        Assign the client a device id.
        """
        self.device_id = str(uuid.uuid4())
        self.sock.write(encode({
            "device_id" : self.device_id,
            "command" : "assign_device_id",
        }))
        self._server().save_device_id(self.device_id)

    def cycle(self):
        """
        Read new data from the client, and do any processing if
        necessary.
        """
        try:
            new_data = self.sock.read()
        except ssl.SSLError:
            new_data = ""
        if new_data:
            self.pending += new_data
            packets, remainder = decode(self.pending)
            if packets:
                self.pending = remainder
                for packet in packets:
                    self._server().check_message(self, packet)

        
class SlockyServer(object):
    """
    """
    def __init__(self, host, port, server_dir):
        self._certfile = abspath(joinpath(server_dir, "certfile"))
        self._keyfile = abspath(joinpath(server_dir, "keyfile"))
        self._ids_file = abspath(joinpath(server_dir, "devices"))

        self._timeout_period = 60*5 # five minutes
       
        try:
            assert os.path.isfile(self._certfile)
            assert os.path.isfile(self._keyfile)
        except AssertionError:
            self._cert_setup(server_dir)

        self._socket_setup(host, port)
        
    def _cert_setup(self, server_dir):
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

        # Actually what follows seems to work fine now.  Huh.  Leaving
        # the above comment incase it doesn't again...?

        assert os.path.isdir(server_dir)
        cmd = "openssl req -x509 -newkey rsa:4096 -keyout {0}"
        cmd += " -out {1} -days 365 -passout pass:{2}"

        tmp_file = tempfile.mkstemp()[1]

        passwd = str(uuid.uuid4())
        args = cmd.format(
            tmp_file, self._certfile, passwd).split(" ")

        # generate an ssl cert and key
        proc = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        proc.communicate("\n"*7) # HACK, pass 7 returns to use defaults

        # generate a passwordless key
        args = "openssl pkey -in {0} -out {1} -passin pass:{2}".format(
                tmp_file, self._keyfile, passwd).split(" ")
        proc = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        proc.communicate()

        # delete the passworded key
        os.remove(tmp_file)
        
    def _socket_setup(self, host, port):
        """
        Open and listen to our socket 
        """
        
        self._s = socket.socket()
        self._s.bind((host, port))
        self._s.listen(5)
        self._s.setblocking(0)
        self._sockets = []
        self._clients = []
        self._devices = []

        if os.path.isfile(self._ids_file):
            with open(self._ids_file, "r") as ids_file:
                self._devices = ids_file.read().strip().split("\n")

        self._nossl_s = socket.socket()
        self._nossl_s.bind((host, port+1))
        self._nossl_s.listen(5)
        self._nossl_s.setblocking(0)

        self._pending = None

    def _connect_client(self, socket, address):
        """
        Connects a new client over ssl.
        """
        ssl_wrapper = ssl.wrap_socket(
            socket, server_side=True,
            certfile = self._certfile,
            keyfile = self._keyfile,
            ssl_version = ssl.PROTOCOL_TLSv1)
        client = ClientConnection(self, ssl_wrapper, address)
        self._clients.append(client)
        return client

    def _check_pair_expiration(self, sock, addr):
        """
        Checks to see if a pending device pairing has expired.  Serves an
        error message to the client if it has; returns True if the
        pair expired and False if it is still good.
        """

        stamp = time.time() - self._pending[1]
        if stamp > self._timeout_period:
            # passphrase expired
            sock.send("ERROR:Device pairing expired.")
            sock.close()
            self._pending = None
            return True
        else:
            return False

    def _serve_cert(self, sock, addr):
        """
        Serves a certificate and a salted checksum in the clear, closes out
        the socket connection.
        """

        if not self._check_pair_expiration(sock, addr):
            with open(self._certfile, "r") as certfile:
                cert_data = certfile.read()
            salt = self._pending[0]
            checksum = hashlib.sha512(salt+cert_data).hexdigest()
            msg = "CERT:{0}:{1}:{2}".format(len(checksum), checksum, cert_data)
            sock.send(msg)
            sock.close()

    def save_device_id(self, device_id):
        """
        Save a client's newly assigned device_id so that they can connect
        again later on.
        """
        assert device_id is not None
        self._devices.append(device_id)
        with open(self._ids_file, "a") as id_cache:
            id_cache.write(str(device_id)+"\n")
        
    def check_message(self, client, packet):
        """
        Handles data from the client, calls on_message if the data doesn't
        pertain to the communication layer itself.  If the client
        connection hasn't provided a device id, then messages from the
        client won't be processed.
        """
        data = packet["data"]
        ignore = True
        if data.has_key("command"):
            if data["command"] == "req_device_id" \
               and data.has_key("tmp_phrase"):
                if data["tmp_phrase"] == self._pending[0]:
                    if not self._check_pair_expiration(client.sock, client.addr):
                        self._pending = None
                        client.assign_device_id()
                else:
                    raise NotImplementedError("bad pass phrase for req_device_id")

        # FIXME: determine when the client should not be ignored
        if not ignore:
            self.on_message(client, packet)

    def process_events(self):
        """
        Schedule this somewhere, to process incoming events.
        """

        # readable, writeable, errored
        read_list = [self._s, self._nossl_s] if self._pending \
                    else [self._s]
        # use select to make listening for new connections to be
        # non-blocking
        for s in select.select(read_list, [], [], 0)[0]:
            if s is self._s:
                # make note of any incoming connections
                client = self._connect_client(*self._s.accept())
                # TODO: log this?
            elif s is self._nossl_s:
                # send the cert and salted checksum and then close the
                # connection
                self._serve_cert(*self._nossl_s.accept())
        # client.sock.read() is non-blocking, so we don't need to do
        # anything fancy to see if there is new data or not in a
        # timely fashion.
        for client in self._clients:
            client.cycle()
        
    def on_message(self, client, packet):
        """
        Duckpunch me lol.
        """
        print "New data from {0}: {1}".format(
            client.addr, str(packet["data"]))
    
    def send_message(self, data, clients=None):
        """
        Encapsulates data as packets, and sends to the specified clients.
        If clients is None, this broadcasts the data to all clients.
        """
        packet = encode(data)

        if not clients:
            clients = self.clients

        for client in clients:
            # may or may not be correct
            clients.sock.write(packet)

    def add_new_device(self):
        """
        Generate a pass phrase for passing the cert to a new client.
        Note, that if there is already a pending pairing, this will
        effectively expire the previous pairing.
        """
        
        magic_words = []
        words = [i for i in BASIC_ENGLISH if len(i) >=4]
        random.shuffle(words)
        magic_words = words[:4]

        device_code = " ".join(magic_words)

        self._pending = (device_code, time.time())
        return device_code

    def shutdown(self):
        """
        Close connections and shut down the socket?
        """
        pass
