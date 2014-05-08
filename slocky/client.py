
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




class SlockyClientError(Exception):
    pass




class SlockyClient(object):
    """
    """

    def __init__(self, host, port, client_dir):
        assert os.path.isdir(client_dir)
        self._certfile = abspath(join(client_dir, "certfile"))
        self._id_path = abspath(join(client_dir, "device"))
        self._device_id = None
        # set 'True' to indicate a cached device_id:
        self._prevalidated = False

        if os.path.isfile(self._id_path):
            with open(self._id_path, "r") as id_file:
                self._device_id = id_file.read().strip()

        self._host = host
        self._port = port
        self._connected = False

        self._cert_data = None
        self._cert_checksum = None
        self._passphrase = None
        self._cache = ""

    def connect(self):
        """
        Attempt to connect to the server.
        """
        if not os.path.isfile(self._certfile):
            # first we need to download and validate the server's
            # certificate
            self._cert_fetch()
        else:
            assert self._device_id
            self._prevalidated = True
            self.on_checksum_pass()
                        
    def _cert_fetch(self):
        nossl_s = socket.socket()
        nossl_s.connect((self._host, self._port+1))
        nossl_s.settimeout(1)

        cache = ""
        stream = ""
        
        try:
            while len(cache) == 0 or len(stream) > 0:
                stream = nossl_s.recv(1024)
                cache += stream
            nossl_s.close()
        except socket.timeout:
            pass

        parts = cache[:32].split(":")
        command = parts[0]

        if command == "CERT":
            check_size = int(parts[1])
            check_offset = len("{0}:{1}:".format(command, check_size))

            checksum = cache[check_offset:check_offset+check_size]
            cert_offset = check_offset+check_size+1

            self._cert_checksum = checksum
            self._cert_data = cache[cert_offset:]
            self.on_validate()
            
        else:
            self.on_no_cert_sent()

    def _gen_device_id(self):
        """
        Request a device_id.
        """
        data = {
            "command" : "req_device_id",
            "tmp_phrase" : self._passphrase,
        }
        packet = encode(data)
        self._sock.write(packet)

    def _connect(self):
        """
        Setup the socket.
        """
        self._nossl_s = socket.socket()
        self._sock = ssl.wrap_socket(
            self._nossl_s, ca_certs=self._certfile, 
            cert_reqs=ssl.CERT_REQUIRED)
        self._sock.connect((self._host, self._port))
        self._sock.setblocking(0)

    def validate_device(self, passphrase):
        """
        Call this from within on_validate to validate and hopefully save
        the incoming certificate.
        """
        checksum = hashlib.sha512(passphrase+self._cert_data).hexdigest()
        if self._cert_checksum == checksum:
            # certificate checksum passed!
            self._passphrase = passphrase
            with open(self._certfile, "w") as cert_file:
                cert_file.write(self._cert_data)
            self.on_checksum_pass()
        else:
            # certificate checksum failed
            self.on_checksum_fail(passphrase)

    def _establish_id(self):
        """
        This is called after the client has been paired to the server to
        remind the server of the client's device_id.
        """
        hint = hashlib.sha512(self._device_id).hexdigest()
        data = {
            "command" : "revalidate",
            "device_hint" : hint,
            }
        packet = encode(data)
        self._sock.write(packet)

    def _assign_device_id(self, device_id):
        """
        Sets and saves the assigned device id.
        """
        self._device_id = device_id
        with open(self._id_path, "w") as id_file:
            id_file.write(str(device_id))
        self.on_device_verified()

    def _process_message(self, packet):
        """
        Determine if an event should be raised or not from received
        packets.
        """
        if not self._device_id:
            if packet["data"].has_key("command") and \
               packet["data"]["command"] == "assign_device_id":
                self._assign_device_id(packet["data"]["device_id"])
        else:
            # FIXME: this should probably fail very loudly because it
            # almost certainly means a man-in-the-middle?

            # ... actually maybe we should be using a checksum
            # instead, with the device id as salt rather than ever
            # broadcasting the device id after assignment...

            assert packet["id"] == self._device_id
            self.on_message(packet["data"])
            
    def process_events(self):
        """
        Schedule this somewhere, to process incoming data from the server.
        """
        assert self._connected
        try:
            new_data = self._sock.read()
        except ssl.SSLError:
            new_data = ""
        if new_data:
            self._cache += new_data
            packets, remainder = decode(self._cache)
            if packets:
                self._cache = remainder
                for packet in packets:
                    self._process_message(packet)

    def send(self, data):
        """
        Try to send data to the server.  Data should be json serializable.
        """
        assert self._device_id is not None
        packet = encode(data, self._device_id)
        self._sock.write(packet)

    def on_checksum_pass(self):
        """
        This is called when a certificate checksum passes.  Generally,
        this function should not need to be overridden.  Override
        on_connected instead.
        """
        # if we have a valid certificate, open a new connection
        self._connect()

        if not self._device_id:
            # if we don't yet have a device id established, do
            # that now before doing anything else
            self._gen_device_id()

        if self._prevalidated:
            self._establish_id()

        self._connected = True        
        self.on_connected()

    def on_checksum_fail(self):
        """
        This is called when a certificate checksum fails.
        """
        pass

    def on_validate(self):
        """
        Override me!  This is called when the user needs to enter in the
        "device key" passphrase to validate a new certificate.
        """
        pass

    def on_no_cert_sent(self):
        """
        Override me!  This is called when the client attempts to fetch a
        cert from the server without the server expecting a pairing
        request.
        """
        raise NotImplementedError(
            "Error handling when the cert req is refused")

    def on_message(self, msg_object):
        """
        Override me!  This is called when there is a new event from the
        server.
        """
        pass

    def on_connected(self):
        """
        Override me!  This is called when the client is connected via ssl
        and is able to listen to commands from the server.  THE CLIENT
        IS NOT NECCESARILY ABLE TO SEND AT THIS POINT.
        """
        pass

    def on_device_verified(self):
        """
        Override me! This is called after the connection is established,
        and the client has a valid device ID to use for sending
        communications.  THUS, the client can both send and receive.
        """
        pass

    def shutdown(self):
        """
        Close the client connection.
        """
        try:
            if self._device_id is not None:
                self.send({"command":"shutdown"})
            self._sock.close()
        except:
            # don't care, we're done here
            pass
