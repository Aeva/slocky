

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


def test_cert_fetch():
    """
    Test the process of validating a new client.
    """
    server_dir = tempfile.mkdtemp()
    client_dir = tempfile.mkdtemp()
    test_port = gen_port()

    srv_stop = False
    server = SlockyServer(HOST, test_port, server_dir)
    client = SlockyClient(HOST, test_port, client_dir)

    device_key = server.add_new_device()

    results = {
        "client_prompted" : False,
        "client_connected" : False,
    }

    def srv_thread():
        while not srv_stop:
            server.process_events()
            time.sleep(.1)
        server.shutdown()

    thread = Thread(target=srv_thread)
    thread.start()

    def on_validate():
        client.validate_device(device_key)
        results["client_prompted"] = True

    def on_connected():
        results["client_connected"] = True
        
    client.on_validate = on_validate
    client.on_connected = on_connected

    try:
        client.connect()
        for i in range(10):
            client.process_events()
            time.sleep(.2)
        client.shutdown()
        srv_stop = True
        thread.join()
    except:
        srv_stop = True
        thread.join()
        raise

    assert os.path.isfile(os.path.join(client_dir, "certfile"))
    assert results["client_prompted"] == True
    assert results["client_connected"] == True

    client_id = str(client._device_id)
    client_id_path = client._idfile
    server_ids = server._devices
    server_ids_path = server._ids_file
    
    assert client_id is not None
    assert server_ids.count(client_id) == 1
    assert os.path.isfile(client_id_path)
    assert os.path.isfile(server_ids_path)


def test_bad_checksum():
    """
    In this test we give the client a bad pass phrase, so that the
    checksum will fail from the cert.  The client class should both
    refuse to store the cert, as well as raise an error of some kind.
    """
    server_dir = tempfile.mkdtemp()
    client_dir = tempfile.mkdtemp()
    test_port = gen_port()

    class TestClient(SlockyClient):
        def __init__(self, bad_passphrase):
            SlockyClient.__init__(self, HOST, test_port, client_dir)
            self.checksum_failed = False
            self.bad_passphrase = bad_passphrase

        def on_validate(self):
            self.validate_device(self.bad_passphrase)
            
        def on_checksum_fail(self, pass_phrase):
            self.checksum_failed = True


    class TestServer(SlockyServer, Thread):
        def __init__(self):
            SlockyServer.__init__(self, HOST, test_port, server_dir)
            Thread.__init__(self)
            self.__stop = False

        def run(self):
            while not self.__stop:
                server.process_events()
                time.sleep(.1)
            self.shutdown()

        def stop(self):
            self.__stop = True
            self.join()

    server = TestServer()
    real_key = server.add_new_device()
    bad_key = "".join([i for i in real_key[::-1]])

    client = TestClient(bad_key)

    try: 
        server.start()
        client.connect()
    except:
        server.stop()
        raise
    server.stop()
    
    assert client.checksum_failed == True


def test_bad_pairing():
    """
    In this test, the client should connect to the server, but then
    attempt to pair with an invalid pass phrase.  The server should
    reply with an error message, and allow the client to try again.
    (Until the pairing times out, but that is the scope of another
    test.)
    """
    assert False


def test_timeout():
    """
    In this test, the client should start performing a device pairing,
    change the timeout value on the server to 0, and fail the device
    pairing.  It should do so for the two phases of the device pairing
    process for which the server checks for timeouts.
    """
    assert False


def test_reconnection():
    """
    This test should connect the client to the server, performing
    pairing etc, and then should disconnect the client, and then
    connect a new client with the same temp directory, send some kind
    of message and receive a reply, without having to be paired.
    """
    assert False


def test_communication():
    """
    This test should connect a client to the server, perform the device
    pairing, send a message, receive a reply, disconnect, reconnect,
    send a message, receive a reply.
    """
    assert False


def test_cold_shoulder():
    """
    A malicious fake client should try to connect to the server without
    performing the device pairing.  The server should ignore all of
    its message requests and deny attempts to authenticate / pair.

    The connection should close with the client trying to send a fake
    device id.
    """
    assert False
