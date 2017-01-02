"""
Handles the reading and processing of seating charts.
"""
import re
import csv

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
            return None
        match = re.search(r"(Front|Desk).*", seat)
        if match:
            return None # TODO handle these better
        print(seat)
        raise RuntimeError(seat)
    def __repr__(self):
        return "Location(room={!r}, row={!r}, column={!r})".format(self.room, self.row, self.column)

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
