
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


TEST_PORT = random.randint(49152, 65534)


def test_cert_generation():
    server_dir = tempfile.mkdtemp()
    s = SlockyServer('localhost', TEST_PORT, server_dir)
    assert os.path.isfile(os.path.join(server_dir, "certfile"))
    assert os.path.isfile(os.path.join(server_dir, "keyfile"))


# def test_msg_pass():
#     server_dir = tempfile.mkdtemp()
#     cert_path = os.path.join(server_dir, "certfile")
#     test_phrase = "I'm a hedgehog!\n"
#     srv_stop = False
#     results = {
#         "received" : False,
#         "data" : [],
#     }

#     srv = SlockyServer('localhost', TEST_PORT, server_dir)
#     def msg_handler(client, packet):
#         results["received"] = True
#         results["data"].append(packet["data"])
#     srv.check_message = msg_handler

#     def srv_thread():
#         while not srv_stop:
#             srv.process_events()            
#             time.sleep(.1)
#         srv.shutdown()

#     thread = Thread(target = srv_thread)
#     thread.start()
#     try:
#         s = socket.socket()
#         s.settimeout(1)
#         ssl_sock = ssl.wrap_socket(
#             s, ca_certs=cert_path, cert_reqs=ssl.CERT_REQUIRED)
#         ssl_sock.connect(('localhost', TEST_PORT))
#         ssl_sock.write(encode(test_phrase))
#         srv_stop = True
#         thread.join()
#     except:
#         srv_stop = True
#         thread.join()
#         raise

#     assert results["received"]
#     assert results["data"][0] == test_phrase


def test_new_device_phrase_gen():
    """
    Tests the add new device function to be sure it gives different
    results each time for the pass pharse.
    """

    server_dir = tempfile.mkdtemp()
    srv = SlockyServer('localhost', TEST_PORT, server_dir)
    key_a = srv.add_new_device()
    key_b = srv.add_new_device()
    assert key_a != key_b
