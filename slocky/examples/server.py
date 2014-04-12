
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


import time
import tempfile
from slocky.server import SlockyServer


PORT = 14900
HOST = 'localhost'
SERVER_DIR = tempfile.mkdtemp()


class ExampleServer(SlockyServer):
    def __init__(self):
        SlockyServer.__init__(self, HOST, PORT, SERVER_DIR)

    def loop_forever(self):
        """
        Run the server's event loop until the process is killed.

        Generate a new device pairing key and print it to the console
        whenever there is no pending pairing.
        """
        print "Starting server main loop..."
        while True:
            if self._pending is None:
                msg =  " - Use this pass phrase to validate a new device:\n"
                msg += ' - - "{0}"\n'
                print msg.format(self.add_new_device())
            self.process_events()
            time.sleep(.1)

    def on_message(self, client, data):
        client.send({
            "alert" : "The server has received your message.",
            })
        for other_client in self._clients:
            if other_client is not client:
                other_client.send(data)


if __name__ == "__main__":
    s = ExampleServer()
    s.loop_forever()
