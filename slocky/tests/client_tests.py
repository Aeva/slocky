

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


import tempfile, random, time, os, ssl, socket
from threading import Thread

from slocky.server import *
from slocky.client import *


HOST = 'localhost'
def gen_port():
    return random.randint(49152, 65534)




class BasicServer(SlockyServer, Thread):
    def __init__(self, test_port):
        self.server_dir = tempfile.mkdtemp()
        SlockyServer.__init__(self, HOST, test_port, self.server_dir)
        Thread.__init__(self)
        self.__stop = False

        self.called_on_message = False

    def run(self):
        while not self.__stop:
            self.process_events()
            time.sleep(.1)
        self.shutdown()

    def stop(self):
        self.__stop = True
        self.join()

    def on_message(self, client, packet):
        self.called_on_message = True




class BasicClient(SlockyClient):
    def __init__(self, test_port, validation_phrase):
        self.client_dir = tempfile.mkdtemp()
        SlockyClient.__init__(self, HOST, test_port, self.client_dir)
        self.validation_phrase = validation_phrase

        self.called_on_checksum_fail = False
        self.called_on_validate = False
        self.called_on_message = False
        self.called_on_connected = False

    def on_validate(self):
        self.called_on_validate = True
        self.validate_device(self.validation_phrase)                             

    def on_checksum_fail(self, passphrase):
        self.called_on_checksum_fail = True

    def on_connected(self):
        self.called_on_connected = True

    def on_message(self):
        self.called_on_message = True




def test_cert_fetch():
    """
    Test the process of validating a new client.
    """
    test_port = gen_port()
    server = BasicServer(test_port)
    client = BasicClient(test_port, server.add_new_device())
    try:
        server.start()
        client.connect()
        for i in range(10):
            client.process_events()
            if client._device_id:
                break
            time.sleep(.2)
        client.shutdown()
        server.stop()
        server.join()
    except:
        server.stop()
        server.join()
        raise

    assert os.path.isfile(os.path.join(client.client_dir, "certfile"))
    assert client.called_on_validate
    assert client.called_on_connected

    client_id = str(client._device_id)
    server_ids = server._devices
    
    assert client_id is not None
    assert server_ids.count(client_id) == 1
    assert os.path.isfile(client._id_path)
    assert os.path.isfile(server._ids_path)


def test_bad_checksum():
    """
    Test client reacting to a bad pass phrase when checking the cert
    checksum.  Client should both refuse to store the cert as well as
    call an event.
    """
    test_port = gen_port()
    server = BasicServer(test_port)
    real_key = server.add_new_device()
    bad_key = "".join([i for i in real_key[::-1]])
    client = BasicClient(test_port, bad_key)
    try: 
        server.start()
        client.connect()
        server.stop()
    except:
        server.stop()
        raise
    
    assert client.called_on_checksum_fail == True
    assert os.path.isfile(client._certfile) == False


def test_bad_pairing():
    """
    Send bad pairing phrase to server.

    In this test, the client should connect to the server, but then
    attempt to pair with an invalid pass phrase.  The server should
    reply with an error message, and then close the connection.

    In some higher paranoia state, a pending device pairing should
    just be canceled.  The rational being is that the client has the
    ability via the checksum to do "bad password, try again" until
    they get it right; thus when the client actually sends a request,
    it is reasonable to assume that if it is not correct the first
    time, it won't be on subsequent tries (and is probably malicious?)
    """

    test_port = gen_port()
    server = BasicServer(test_port)
    real_key = server.add_new_device()
    bad_key = "".join([i for i in real_key[::-1]])
    client = BasicClient(test_port, real_key)
    
    def gen_device_id():
        """
        Request a device_id.
        """
        data = {
            "command" : "req_device_id",
            "tmp_phrase" : bad_key,
        }
        packet = encode(data)
        client._sock.write(packet)

    client._gen_device_id = gen_device_id

    try: 
        server.start()
        client.connect()
        for i in range(10):
            client.process_events()
            if client._device_id:
                break
            time.sleep(.2)
        server.stop()
        server.join()
    except:
        server.stop()
        raise
    
    assert not client._device_id


def test_communication():
    """
    Client-server communication test.

    This test should connect a client to the server, perform the device
    pairing, send a message, receive a reply, disconnect, reconnect,
    send a message, receive a reply.
    """

    test_port = gen_port()
    server = BasicServer(test_port)
    client = BasicClient(test_port, server.add_new_device())

    def srv_on_message(client, data):
        server.called_on_message = True
        if data.has_key('command') and data['command'] == "echo":
            client.send({
                "command" : "alert",
                "phrase" : data["phrase"],
            })
    server.on_message = srv_on_message

    client.echos = []
    def cli_on_message(msg_data):
        client.called_on_message = True
        if msg_data["command"] == "alert":
            client.echos.append(msg_data["phrase"])
    client.on_message = cli_on_message

    try: 
        server.start()
        client.connect()

        for i in range(5):
            client.process_events()
            if client._device_id:
                break
            time.sleep(.2)

        client.send({
            "command" : "echo",
            "phrase" : "first message",
        })
        client.send({
            "command" : "echo",
            "phrase" : "second message",
        })

        for i in range(5):
            client.process_events()
            time.sleep(.2)
        server.stop()
        server.join()
    except:
        server.stop()
        raise

    assert server.called_on_message
    assert len(client.echos) == 2
    assert client.echos[0] == "first message"
    assert client.echos[1] == "second message"


def test_cert_req_refused():
    """
    Client response for when server refuses to serve cert.
    """
    assert False


def test_reconnection():
    """
    Client reconnection test.
    
    This test should connect the client to the server, performing
    pairing etc, and then should disconnect the client, and then
    connect a new client with the same temp directory, send some kind
    of message and receive a reply, without having to be paired.
    """
    assert False


def test_timeout():
    """
    Pairing timeout test.

    In this test, the client should start performing a device pairing,
    change the timeout value on the server to 0, and fail the device
    pairing.  It should do so for the two phases of the device pairing
    process for which the server checks for timeouts.
    """
    assert False


def test_cold_shoulder():
    """
    Ignore a malicious client.

    A malicious fake client should try to connect to the server without
    performing the device pairing.  The server should ignore all of
    its message requests and deny attempts to authenticate / pair.

    The connection should close with the client trying to send a fake
    device id.
    """
    assert False
