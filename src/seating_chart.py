import re
import csv

class Location:
    def __init__(self, room, row, column):
        self.room = room
        self.row = row
        self.column = column
    @staticmethod
    def create_location(room, seat):
        m = re.search(r"([A-Za-z])([0-9]+)", seat)
        if m:
            return Location(room, int(m.group(2)), ord(m.group(1)) - ord('A'))
        m = re.search(r"Row (\d+), Table ([A-Z]+), Seat ([i]+)", seat)
        if m:
            roman = {"i" : 1, "ii" : 2, "iii" : 3, "iv" : 4}[m.group(3)]
            return Location(room, int(m.group(1)), (ord(m.group(2)) - ord('A'), roman))
        m = re.search(r"N/A|FALSE", seat)
        if m:
            return None
        m = re.search(r"(Front|Desk).*", seat)
        if m:
            return None # TODO handle these better
        print(seat)
        raise RuntimeError(seat)
    def __repr__(self):
        return "Location(room={!r}, row={!r}, column={!r})".format(self.room, self.row, self.column)

def read_seating_chart(seat_file):
    with open(seat_file) as fil:
        data = list(csv.reader(fil))
    email_loc = data[0].index("Email Address")
    seat_loc = data[0].index("Seat")
    room_loc = data[0].index("Room")
    return {x[email_loc] : Location.create_location(x[room_loc], x[seat_loc]) for x in data[1:]}
