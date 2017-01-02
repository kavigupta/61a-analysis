import re

class Location:
    def __init__(self, room, row, column):
        self.room = room
        self.row = row
        self.column = column
    @staticmethod
    def create_location(room, seat):
        m = re.search(r"([A-Za-z]+)([0-9]+)", seat)
        if m:
            return Location(room, ord(m.group(1)) - ord('A'), int(m.group(2)))
        m = re.search(r"N/A", seat)
        if m:
            return None
        raise RuntimeError(str(room, seat))
    def __repr__(self):
        return "Location(room={!r}, row={!r}, column={!r})".format(self.room, self.row, self.column)