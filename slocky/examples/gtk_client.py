
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
import os
import time
import tempfile

from gi.repository import Gtk, GObject

from slocky.client import SlockyClient


CLIENT_DIR = tempfile.mkdtemp()


class GladeClient(SlockyClient):
    def __init__(self):
        """
        Note that the SlockyClient's base class in this example is
        initialized by the on_connect_button_pressed method.
        SlockyClient methods should not be called until then.
        """
        glade_path = os.path.join(
            os.path.split(__file__)[0],
            "example_ui.glade")

        self.__builder = Gtk.Builder()
        self.__builder.add_from_file(glade_path)
        self.__builder.connect_signals(self)

        self.__ct_prompt = self.__builder.get_object("connection_prompt")
        self.__ct_prompt.show_all()

    def on_exit(self, *args):
        """
        Called when the client closes.
        """
        Gtk.main_quit()

    def on_connect_button_pressed(self, *args):
        """
        Called when the user has input the server to connect to.
        (See "connection_propmt" gtk window in the glade file)
        """
        try:
            host = self.__builder.get_object("host_entry").get_text()
            port = self.__builder.get_object("port_entry").get_text()
            name = self.__builder.get_object("name_entry").get_text()

            host = host.strip()
            port = int(port.strip())
            name = name.strip()

            assert len(host) > 0
            assert len(name) > 0
        except ValueError:
            return
        except AssertionError:
            return

        win = self.__ct_prompt
        win.hide()

        SlockyClient.__init__(self, host, port, CLIENT_DIR)
        self.connect()

    def on_validate(self):
        """
        This is called when the client has a new SSL cert to validate.
        This method should be used to prompt the user for the checksum
        salt.
        """
        chat = self.__chat = self.__builder.get_object("chat_window")
        vali = self.__vali = self.__builder.get_object("validation_dialog")
        chat.show_all()
        vali.show_all()
        
    def on_validate_button_pressed(self, *args):
        """
        Called after the user has input a hash.  Attempts to validate for
        correctness.  (See "validation_dialog" gtk window in the glade
        file)
        """
        vali_entry = self.__builder.get_object("validation_entry")
        passphrase = vali_entry.get_text().strip()
        match = re.match(r"^[a-z]+ [a-z]+ [a-z]+ [a-z]+$", passphrase)
        if match is not None:
            self.__vali.hide()
            self.validate_device(passphrase)
        else:            
            print "no match"

    def on_checksum_fail(self, *args):
        """
        This is called when the certificate checksum fails with the salt
        provided by the user.  Ideally the user should be notified of
        this and determine if they want to try to enter the salt in
        again or give up.

        User should be also informed of the implications of a possible
        malicious entity.
        """
        print "validation failed"
        # fixme: show an error and make the client try again
        #label = self.__builder.get_object("prompt_label")

    def on_connected(self):
        """
        This is called when the certificate is determined to be valid, and
        a ssl connection to the
        """
        print "SSL connection established."
        self.__pulse_timeout = GObject.timeout_add(50, self.pulse, None)

    def on_device_verified(self):
        print "Client can now send and receive to the server."
        
    def on_post_msg(self, *args):
        """
        Called when the user clicks the 'Add' button in the ui.  If there
        is a message to post, send it to the server and clear the
        input box.
        """
        chat_line = self.__builder.get_object("chat_entry")
        msg = chat_line.get_text()
        chat_line.set_text("")
        self.send({
            "chat" : msg,
            })

    def on_message(self, data):
        print "NEW MESSAGE: " + str(data)
        
    def pulse(self, *args):
        """
        Schedule me to occur periodically.
        """
        self.process_events()
        self.__pulse_timeout = GObject.timeout_add(50, self.pulse, None)

if __name__ == "__main__":
    client = GladeClient()
    try:
        Gtk.main()
    except:
        # fixme: if connection fails, re-show the connection and
        # add an error label or something?
        Gtk.main_quit()
        raise
