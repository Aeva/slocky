

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

TEST_PORT = random.randint(49152, 65534)
HOST = 'localhost'


def test_cert_fetch():
    server_dir = tempfile.mkdtemp()
    client_dir = tempfile.mkdtemp()

    srv_stop = False
    server = SlockyServer(HOST, TEST_PORT, server_dir)
    client = SlockyClient(HOST, TEST_PORT, client_dir)

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
