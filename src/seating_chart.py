"""
Handles the reading and processing of seating charts.
"""
import re
import csv

from functools import total_ordering
from itertools import groupby

from abc import ABCMeta, abstractmethod
from enum import Enum

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
    def relation(self, other):
        """
        Get the relationship between our current column and another one
        """
        basis = min((self.range, other.range))
        sloc, oloc = self.location * basis, other.location * basis
        if sloc == oloc:
            return ColumnRelation.ALIGNED
        if sloc == oloc + 1:
            return ColumnRelation.RIGHT
        if sloc == oloc - 1:
            return ColumnRelation.LEFT
        return ColumnRelation.DOES_NOT_EXIST
    @property
    def range(self):
        """
        The number of possible seats total
        """
        return self.cmax - self.cmin
    @property
    def location(self):
        """
        A rational in [0, 1] representing an abstract concept of horizontal location (percentage
            left to right)
        """
        return (self.val - self.cmin) / (self.cmax - self.cmin)

class ColumnRelation(Enum):
    """
    Represents relationship between column positions.
    """
    LEFT = -1
    RIGHT = 1
    ALIGNED = 0
    DOES_NOT_EXIST = None
    @property
    def sideways(self):
        """
        If it's rightwards or leftwards, not aligned or nonexistant
        """
        return self == ColumnRelation.LEFT or self == ColumnRelation.RIGHT

class AbstractLocation(metaclass=ABCMeta):
    """
    Describes the abstract concept of a location, which might be known or unknown
    """
    @property
    def row_identifier(self):
        """
        Globally unique identifier per row
        """
        return self.room, self.row
    @property
    @abstractmethod
    def room(self):
        """
        The current room
        """
        pass
    @property
    @abstractmethod
    def row(self):
        """
        The current rows
        """
        pass
    @property
    @abstractmethod
    def column(self):
        """
        The current column
        """
        pass

@total_ordering
class Location(AbstractLocation):
    """
    A location at which a student takes an exam
    """
    def __init__(self, room, row, column):
        self.__room = room
        self.__row = row
        self.__column = column
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
    def room(self):
        return self.__room
    @property
    def row(self):
        return self.__row
    @property
    def column(self):
        return self.__column

@total_ordering
class UnknownLocation(AbstractLocation):
    """
    A location which is unknown
    """
    def __lt__(self, other):
        if isinstance(other, UnknownLocation):
            return False
        return True
    def __repr__(self):
        return "unknown"
    @property
    def row(self):
        return unknown
    @property
    def column(self):
        return unknown
    @property
    def room(self):
        return unknown
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
