
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

from gi.repository import Gtk, GObject, Notify

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

        # Initialize notifications
        Notify.init("slocky")

    def on_exit(self, *args):
        """
        Called when the client closes.
        """
        try:
            self.send({"alert": "{0} is signing out.".format(self.user_name)})
        except Exception:
            pass # Oh well, the server should announce this too.
        self.shutdown()
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
            self.user_name = name.strip()

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
        a ssl connection has been established.  At this point in time
        the client can read, but cannot write.

        Calling 'self.process_events()' periodically is necessary to
        finish the pairing process.  In this example, we accomplish
        this via self.pulse, which schedules itself as a recurring
        timeout.
        """
        print "SSL connection established."
        self.pulse()

    def on_device_verified(self):
        """
        This is called after on_connected, as soon as the client has a
        device_id assigned to it.

        Ideally this event is used to indicate to the frontend that it
        is now safe to attempt to send messages to the server.
        """
        self.show_msg("You are now connected to the server.", "alert")
        self.send({"alert": "{0} has connected the server.".format(self.user_name)})

    def on_key_press(self, widget, event):
        # If we hit enter.
        if event.string == "\r":
            self.on_post_msg()
            return True

    def notify(self, message):
        """
        Displays a notification
        """
        window = self.__builder.get_object("chat_window")

        # Don't show notification if window is in focus
        if window.is_active():
            return False

        notification = Notify.Notification.new("Slocky", message, "dialog-information")
        notification.show()
        return True

    def show_msg(self, text, mode, name=None):
        """
        Shows a message in the chat log.
        """
        assert mode in ["alert", "post", "reply"]
        textbuf = self.__builder.get_object("chat_text_buffer")
        end = textbuf.get_end_iter()
        italics = textbuf.create_tag(style="PANGO_STYLE_ITALIC")
        purple = textbuf.create_tag(foreground="#8d0196")
        lime = textbuf.create_tag(foreground="#8dbb00")
        gray = textbuf.create_tag(foreground="#888888")
        if mode == "alert":
            msg = "-->{0}\n".format(text)
            textbuf.insert_with_tags(end, msg, italics, gray)
        elif mode == "post":
            msg = "{0}:".format(self.user_name)
            textbuf.insert_with_tags(end, msg, lime)
            end = textbuf.get_end_iter()
            textbuf.insert(end, " {0}\n".format(text))
        else:
            self.notify("You have a new message from {0}.".format(name))
            msg = "{0}:".format(name)
            textbuf.insert_with_tags(end, msg, purple)
            end = textbuf.get_end_iter()
            textbuf.insert(end, " {0}\n".format(text))

        # Autoscroll to text
        end = textbuf.get_end_iter()
        scrollwindow = self.__builder.get_object("message_body")
        scrollwindow.scroll_to_iter(end, 0, False, 0.5, 0.5)

    def on_post_msg(self, *args):
        """
        This is the event handler for the "add" button, which is used by
        the user to indicate that their message is to be sent to the server.

        (See the 'chat_window' gtk widget in the glade file)
        """
        textbuf = self.__builder.get_object("entry_text_buffer")
        start = textbuf.get_start_iter()
        end = textbuf.get_end_iter()
        msg = textbuf.get_text(start, end, True)
        textbuf.set_text("")
        self.send({
            "chat" : msg,
            "name" : self.user_name,
            })
        self.show_msg(msg, "post")

    def on_message(self, data):
        """
        This event is called when there is a new message from the server.
        """
        name = "Unknown"
        mode = "reply"
        msg = ""
        if data.has_key("alert"):
            mode = "alert"
            msg = data["alert"]
        elif data.has_key("chat"):
            msg = data["chat"]
        if data.has_key("name"):
            name = data["name"]
        if msg:
            if mode == "alert" and \
               msg == "The server has received your message.":
                return #don't care

            self.show_msg(msg, mode, name)
        
    def pulse(self, *args):
        """
        This method schedules itself as a reoccuring timeout.  This allows
        events from the server to be processed.  Without it,
        on_message, and on_device_verified would never be called.
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
