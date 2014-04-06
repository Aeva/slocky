
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


import ssl, socket


from slocky.packet import encode



def test_client():
    s = socket.socket()
    ssl_sock = ssl.wrap_socket(s, ca_certs="certfile", cert_reqs=ssl.CERT_REQUIRED)
    ssl_sock.connect(('localhost', 14900))
    ssl_sock.write(encode("I'm a hedgehog!\n"))
