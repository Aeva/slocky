
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

import json, struct


def encode(data, client_id=None):
    """
    Creates a packet.  Data must be json serializable.  This function
    wraps json.dumps, but also adds transport information.
    """
    p = json.dumps({
        "id" : client_id,
        "data" : data,
        })

    # size is a big-endian formatted unsigned long long (8 bytes)
    size = struct.pack(">Q", len(p))
    
    return size + p


def parse_packet(stream):
    """
    Attempt to decode a packet, and return whatever remains in the
    stream.
    """

    if len(stream) < 8:
        return None, stream

    # size is a big-endian formatted unsigned long long (8 bytes)
    size = struct.unpack(">Q", stream[:8])[0]
    
    packet = None
    remainder = stream
    if len(stream[8:]) >= size:
        packet = json.loads(stream[8:8+size])
        remainder = stream[8+size:]
    return packet, remainder
        

def decode(stream):
    """
    Parse all packets from the stream.  Returns a list of packets, and 
    whatever remains in the stream.
    """
    
    found = []
    remainder = stream
    while len(remainder) > 8:
        packet, remainder = parse_packet(remainder)
        found.append(packet)

    return found, remainder
