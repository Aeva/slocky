
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


import ssl, socket, os, hashlib
from os.path import join as join
from os.path import abspath

from slocky.packet import encode, decode




class SlockyClient(object):
    """
    """

    def __init__(self, host, port, client_dir):
        assert os.path.isdir(client_dir)
        self.__certfile = abspath(join(client_dir, "certfile"))
        self.__idfile = abspath(join(client_dir, "device"))
        self.__device_id = None
        self.__host = host
        self.__port = port
        self.__connected = False

        self.__cert_data = None
        self.__cert_checksum = None
        self.__passphrase = None
        self.__cache = ""

    def connect(self):
        """
        Attempt to connect to the server.
        """
        if not os.path.isfile(self.__certfile):
            # first we need to download and validate the server's
            # certificate
            self.__cert_fetch()

        if os.path.isfile(self.__certfile):
            # if we have a valid certificate, open a new connection
            self.__connect()

            if not self.__device_id:
                # if we don't yet have a device id established, do
                # that now before doing anything else
                self.__gen_device_id()

            if self.__device_id and not self.__connected:
                self.__connected = True
                self.on_connected()
            
    def __cert_fetch(self):
        nossl_s = socket.socket()
        nossl_s.connect((self.__host, self.__port+1))

        cache = ""
        stream = ""
        
        while len(cache) == 0 or len(stream) > 0:
            stream = nossl_s.recv(1024)
            cache += stream
        nossl_s.close()

        parts = cache[:32].split(":")
        command = parts[0]

        if command == "CERT":
            check_size = int(parts[1])
            check_offset = len("{0}:{1}:".format(command, check_size))

            checksum = cache[check_offset:check_offset+check_size]
            cert_offset = check_offset+check_size+1

            self.__cert_checksum = checksum
            self.__cert_data = cache[cert_offset:]
            self.on_validate()
            
        else:
            raise NotImplementedError(
                "Error handling when the cert req is refused")

    def __gen_device_id(self):
        """
        Request a device_id.
        """
        data = {
            "command" : "req_device_id",
            "tmp_phrase" : self.__passphrase,
        }
        packet = encode(data)
        self.__sock.write(packet)

    def __connect(self):
        """
        Setup the socket.
        """
        self.__nossl_s = socket.socket()
        self.__sock = ssl.wrap_socket(
            self.__nossl_s, ca_certs=self.__certfile, 
            cert_reqs=ssl.CERT_REQUIRED)
        self.__sock.connect((self.__host, self.__port))
        self.__sock.setblocking(0)

    def validate_device(self, passphrase):
        """
        Call this from within on_validate to validate and hopefully save
        the incoming certificate.
        """
        checksum = hashlib.sha512(passphrase+self.__cert_data).hexdigest()
        if self.__cert_checksum == checksum:
            # certificate checksum passed!
            self.__passphrase = passphrase
            with open(self.__certfile, "w") as cert_file:
                cert_file.write(self.__cert_data)
        else:
            # certificate checksum failed
            raise NotImplementedError("Handeling of cert checksum failure")

    def __assign_device_id(self, device_id):
        """
        Sets and saves the assigned device id.
        """
        self.__device_id = device_id
        if not self.__connected:
            self.__connected = True
            self.on_connected()

    def __process_message(self, packet):
        """
        Determine if an event should be raised or not from received
        packets.
        """
        if not self.__device_id:
            if packet["data"].has_key("command") and \
               packet["data"]["command"] == "assign_device_id":
                self.__assign_device_id(packet["data"]["device_id"])
        else:
            raise NotImplementedError(
                "message processing when client has a device id")
            
    def process_events(self):
        """
        Schedule this somewhere, to process incoming data from the server.
        """
        try:
            new_data = self.__sock.read()
        except ssl.SSLError:
            new_data = ""
        if new_data:
            self.__cache += new_data
            packets, remainder = decode(self.__cache)
            if packets:
                self.__cache = remainder
                for packet in packets:
                    self.__process_message(packet)

    def on_message(self, msg_object):
        """
        Override me!  This is called when there is a new event from the
        server.
        """
        pass

    def on_connected(self):
        """
        Override me!  This is called when the client is connected to the
        server and is ready to send and receive commands.
        """
        pass

    def on_validate(self):
        """
        Override me!  This is called when the user needs to enter in the
        "device key" passphrase to validate a new certificate.
        """
        pass

    def shutdown(self):
        """
        Close the client connection.
        """
        self.__sock.close()
