
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

from slocky.packet import encode, decode, parse_packet


def test_parse_packet():
    """
    Tests the encode function as well as the parse_packet function.
    """
    test_data = range(10)
    stream = encode(test_data)
    stream += encode("hello")
    stream += encode({
        "foo" : "abc",
        "bar" : "100",
    })
    
    packet, remainder = parse_packet(stream)
    assert packet is not None
    assert packet["data"] == test_data
    assert len(remainder) > 0


def test_decode():
    """
    Tests the decode function.
    """

    test_dict = {
        "foo" : "abc",
        "bar" : 100,
    }

    stream = encode(range(10))
    stream += encode("hello")
    stream += encode(test_dict)
    
    packets, remainder = decode(stream)
    assert len(packets) == 3
    assert len(remainder) == 0

    test1 = packets[0]["data"]
    test2 = packets[1]["data"]
    test3 = packets[2]["data"]

    assert test1 == range(10)
    assert test2 == "hello"
    assert test3["foo"] == "abc"
    assert test3["bar"] == 100


def test_incomplete_parse_packet():
    """
    Tests to be sure the parse_packet function behaves correctly when
    incompleted data is passed to it.
    """
    for test in ["", "DERP"]:
        packet, remainder = parse_packet(test)
        assert packet == None
        assert remainder == test


    


def test_incomplete_decode():
    """
    Tests to be sure the decode function behaves correctly when
    incomplete data is passed to it.
    """
    for test in ["", "DERP"]:
        packet, remainder = decode(test)
        assert packet == []
        assert remainder == test
