
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


import re
import time
import tempfile
from threading import Thread
from slocky.client import SlockyClient


PORT = 14900
HOST = 'localhost'
CLIENT_DIR = tempfile.mkdtemp()


class ExampleClient(SlockyClient, Thread):
    def __init__(self):
        SlockyClient.__init__(self, HOST, PORT, CLIENT_DIR)
        Thread.__init__(self)

    def loop_forever(self):
        self.connect()

    def on_validate(self):
        passphrase = ""
        while re.match(r"^[a-z]+ [a-z]+ [a-z]+ [a-z]+$", passphrase) is None:
            passphrase = raw_input("*** enter pass phrase> ")
        self.validate_device(passphrase)

    def on_checksum_fail(self, passphrase):
        print "Checksum failed.  Please try again:"
        self.on_validate()

    def run(self):
        """
        Listen for data from the server in the background.
        """
        while True:
            self.process_events()
            time.sleep(.1)

    def on_connected(self):
        """
        Client has been validate, awaiting device id.  Drop into event
        loop.
        """
        print "Entering client event loop..."
        while self._device_id is not None:
            self.process_events()
            time.sleep(.1)
        self.start()
        while True:
            data = raw_input("--> ")
            if data:
                self.send({
                    "chat" : data,
                })
            time.sleep(.1)

    def on_message(self, data):
        print "NEW MESSAGE: " + str(data)


if __name__ == "__main__":
    c = ExampleClient()
    c.loop_forever()

