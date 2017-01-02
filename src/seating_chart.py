"""
Handles the reading and processing of seating charts.
"""
import re
import csv

from functools import total_ordering
from itertools import groupby

class Column:
    """
    Represents a column, along with bounds on that particular row's values to normalize comparisons
    """
    def __init__(self, val, cmin, cmax):
        self.val = val
        self.cmin = cmin
        self.cmax = cmax
    def __repr__(self):
        return "Column(val={}, cmin={}, cmax={})".format(self.val, self.cmin, self.cmax)

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
    @property
    def row_identifier(self):
        """
        Globally unique identifier per row
        """
        return self.room, self.row

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
    return [(x[email_loc], Location.create_location(x[room_loc], x[seat_loc])) for x in data[1:]]

def normalize_columns_in_chart(seating_chart):
    """
    Converts tuple columns into single numbers. Sets up minima and maxima for each column and places
        everything into Column objects.
    """
    unknowns = [x for x in seating_chart if isinstance(x[1], UnknownLocation)]
    knowns = [x for x in seating_chart if not isinstance(x[1], UnknownLocation)]
    knowns.sort(key=lambda x: x[1])
    yield from unknowns
    for _, grouped_items in groupby(knowns, key=lambda x: x[1].row_identifier):
        grouped_items = list(grouped_items)
        raw_col = [x[1].column for x in grouped_items]
        if isinstance(raw_col[0], tuple):
            number_per_table = max([v for _, v in raw_col])
            columns = [number_per_table * u + v for u, v in raw_col]
        else:
            columns = raw_col
        min_of_current = min(columns)
        max_of_current = max(columns)
        for email_loc, adjusted_col in zip(grouped_items, columns):
            email, loc = email_loc
            bounded_col = Column(adjusted_col, min_of_current, max_of_current)
            yield email, Location(loc.room, loc.row, bounded_col)

def get_seating_chart(seat_file):
    """
    Performs process of getting a seating chart from a file and normalizing the columns.
    """
    return list(normalize_columns_in_chart(read_seating_chart(seat_file)))
