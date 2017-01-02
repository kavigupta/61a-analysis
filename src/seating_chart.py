"""
Handles the reading and processing of seating charts.
"""
import re
import csv

from functools import total_ordering

@total_ordering
class Location:
    """
    A location at which a student takes an exam
    """
    def __init__(self, room, row, column):
        self.room = room
        self.row = row
        self.column = column
    @staticmethod
    def create_location(room, seat):
        """
        Parses a seat number
        """
        match = re.search(r"([A-Za-z])([0-9]+)", seat)
        if match:
            return Location(room, int(match.group(2)), ord(match.group(1)) - ord('A'))
        match = re.search(r"Row (\d+), Table ([A-Z]+), Seat ([i]+)", seat)
        if match:
            roman = {"i" : 1, "ii" : 2, "iii" : 3, "iv" : 4}[match.group(3)]
            return Location(room, int(match.group(1)), (ord(match.group(2)) - ord('A'), roman))
        match = re.search(r"N/A|FALSE", seat)
        if match:
            return unknown
        match = re.search(r"(Front|Desk).*", seat)
        if match:
            return unknown # TODO handle these better
        print(seat)
        raise RuntimeError(seat)
    def __repr__(self):
        return "Location(room={!r}, row={!r}, column={!r})".format(self.room, self.row, self.column)
    def __lt__(self, other):
        if isinstance(other, UnknownLocation):
            return False
        return (self.room, self.row, self.column) < (other.room, other.row, other.column)

@total_ordering
class UnknownLocation:
    """
    A location which is unknown
    """
    def __lt__(self, other):
        if isinstance(other, UnknownLocation):
            return False
        return True
    def __repr__(self):
        return "unknown"
unknown = UnknownLocation()

def read_seating_chart(seat_file):
    """
    Reads a seating chart from a file
    """
    with open(seat_file) as fil:
        data = list(csv.reader(fil))
    email_loc = data[0].index("Email Address")
    seat_loc = data[0].index("Seat")
    room_loc = data[0].index("Room")
    return {x[email_loc] : Location.create_location(x[room_loc], x[seat_loc]) for x in data[1:]}
