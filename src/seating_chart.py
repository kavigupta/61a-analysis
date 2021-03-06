"""
Handles the reading and processing of seating charts.
"""

import re
import csv

from functools import total_ordering
from itertools import groupby
from collections import defaultdict

from abc import ABCMeta, abstractmethod
from enum import Enum

from numpy import argmin, mean

class SeatingChart:
    """
    Represents a graph of student seating locations.
    """
    def __init__(self, file_loc):
        self.__file_loc = file_loc
        self.__seating_chart = _get_seating_chart(file_loc)
        self.__adjacency = _get_direction_dictionary(self.__seating_chart)
        self.__by_room = {}
        for email in self.emails:
            room = self.room_for(email)
            if room is None:
                continue
            if room not in self.__by_room:
                self.__by_room[room] = []
            self.__by_room[room].append(email)
        self.__adjacency_set = defaultdict(set)
        for email, result in self.__adjacency.items():
            self.__adjacency_set[email] = set(result.values())
        self.__sideways_set = defaultdict(set)
        self.__frontback_set = defaultdict(set)
        for email, result in self.__adjacency.items():
            for direction in result:
                if direction.is_sideways:
                    self.__sideways_set[email].add(result[direction])
                else:
                    self.__frontback_set[email].add(result[direction])

    def __repr__(self):
        return "SeatingChart({!r})".format(self.__file_loc)
    def adjacent_to(self, email, adjacency_type):
        """
        Gets all people adjacent to the given person.
        """
        return {
            AdjacencyType.sideways_only : self.__sideways_set,
            AdjacencyType.forward_backward : self.__frontback_set,
            AdjacencyType.all_ways : self.__adjacency_set
        }[adjacency_type][email]
    def adjacency_layers(self, email, up_to, adjacency_type):
        """
        Gets a list from 0..up_to-1 of sets. The ith list contains every email i away from the
            current email.
        """
        prev_layer = {email}
        seen = {email}
        for _ in range(up_to):
            layer = {new_email
                     for prev_email in prev_layer
                     for new_email in self.adjacent_to(prev_email, adjacency_type)
                     if new_email not in seen}
            seen.update(layer)
            yield layer
            prev_layer = layer
    def similarity_layers(self, email, up_to, adjacency_type, evals, similarity_fn,
                          gambler_fallacy_allowable_limit):
        """
        Gets all layers from 0..up_to-1 of numbers. The ith element contains the average similarity
            between email and all the values with i students between them.
        """
        for layer in self.adjacency_layers(email, up_to, adjacency_type):
            values = [similarity_fn(evals.evaluation_for(email),
                                    evals.evaluation_for(other_email))
                      for other_email in layer
                      if other_email in evals.emails
                      and evals.time_diff(email, other_email) <= gambler_fallacy_allowable_limit]
            if values == []:
                yield float('nan')
            else:
                yield mean(values)

    def all_adjacencies(self, zero_meaned, up_to, adjacency_type, gambler_fallacy_allowable_limit):
        """
        Gets a list from 0..up_to-1 of lists of pairs. The ith list contains pairs of emails of
            students with i students between them.
        """
        adjacencies = [[] for _ in range(up_to)]
        for email in zero_meaned.emails:
            layers = self.adjacency_layers(email, up_to, adjacency_type)
            evalu = zero_meaned.evaluation_for(email)
            for adj, layer in zip(adjacencies, layers):
                for other_email in layer:
                    if other_email not in zero_meaned.emails:
                        continue
                    if zero_meaned.time_diff(email, other_email) <= gambler_fallacy_allowable_limit:
                        continue
                    adj.append((evalu, zero_meaned.evaluation_for(other_email)))
        return adjacencies

    def are_adjacent(self, first, second, adjacency_type):
        """
        Checks whether FIRST and SECOND are adjacent.
        """
        return first in self.adjacent_to(second, adjacency_type) \
                     or second in self.adjacent_to(first, adjacency_type)
    def same_room(self, first, second):
        """
        Returns whether FIRST and SECOND are in the same room.
        """
        first_room = self.room_for(first)
        second_room = self.room_for(second)
        if first_room is None or second_room is None:
            return False
        return first_room.room == second_room.room
    @property
    def emails_by_room(self):
        """
        Output:
            an iterable (room name, list of emails)
        """
        return self.__by_room.items()
    def sideways_items(self, email):
        """
        Get the items sideways of the given email.
        """
        for direction, adj_email in self.__adjacency[email].items():
            if direction.is_sideways:
                yield adj_email
    @property
    def emails(self):
        """
        The entire set of vertices in this graph, which are emails.
        """
        return self.__seating_chart.keys()
    def room_for(self, email):
        """
        Gets the room in which the person with that email lies.
        """
        loc = self.__seating_chart.get(email, None)
        if loc is None:
            return None
        return loc.room
    def y_region(self, email):
        """
        Get the y region (top, middle, bottom) of the given email.
        """
        return self._location(email).y_region
    def _location(self, email):
        return self.__seating_chart[email]

class AdjacencyType(Enum):
    """
    Represents an adjacency type, or a way in which things can be adjacent in a seating chart
    """
    sideways_only = "-"
    forward_backward = "|"
    all_ways = "+"
    def __str__(self):
        return self.value

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
        sloc, oloc = round(self.location * basis), round(other.location * basis)
        if sloc == oloc:
            return ColumnRelation.ALIGNED
        if sloc == oloc + 1:
            return ColumnRelation.RIGHT
        if sloc == oloc - 1:
            return ColumnRelation.LEFT
        return ColumnRelation.DOES_NOT_EXIST
    def closest(self, others):
        """
        Gets the index of the closest value in OTHERS to this one by location.
        """
        arg = argmin([abs(self.location - other.location) for other in others])
        return arg
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
        if self.cmax == self.cmin:
            return 0.5
        return (self.val - self.cmin) / (self.cmax - self.cmin)

class Direction(Enum):
    """
    Represents a compass direction
    """
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    DOWN = (0, -1)
    UPWARDS = (0, 1)
    @property
    def is_sideways(self):
        """
        Whether a direction is left or right.
        """
        return self in (Direction.LEFT, Direction.RIGHT)

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
    @property
    def direction_for(self):
        """
        Get the direction for the given column relation.

        Only defined when sideways is true.
        """
        if self == ColumnRelation.LEFT:
            return Direction.LEFT
        elif self == ColumnRelation.RIGHT:
            return Direction.RIGHT
        else:
            raise TypeError("{} cannot be coerced into a direction".format(self))

@total_ordering
class Row:
    """
    Represents a bounded row.
    """
    def __init__(self, val, rmin, rmax):
        self.__val = val
        self.__rmin = rmin
        self.__rmax = rmax
    def __lt__(self, other):
        # pylint: disable=W0212
        return self.__val < other.__val
    def __eq__(self, other):
        # pylint: disable=W0212
        return self.__val == other.__val
    def __hash__(self):
        return hash(self.__val)
    def move(self, y_off):
        """
        Move the given row in that direction, returning the new value.
        """
        return Row(self.__val + y_off, self.__rmin, self.__rmax)
    @property
    def __y_loc(self):
        return (self.__val - self.__rmin) / (self.__rmax - self.__rmin)
    @property
    def y_region(self):
        """
        Returns whether we're in the front, middle, or back of the room.
        """
        if self.__y_loc < 1 / 3:
            return "front"
        elif self.__y_loc < 2 / 3:
            return "middle"
        else:
            return "back"

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
    @property
    @abstractmethod
    def y_region(self):
        """
        The region (top, middle, bottom) this is in.
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
            return Location(room, row=ord(match.group(1)) - ord('A'), column=int(match.group(2)))
        match = re.search(r"Row (\d+), Table ([A-Z]+), Seat ([i]+)", seat)
        if match:
            roman = {"i" : 1, "ii" : 2, "iii" : 3, "iv" : 4}[match.group(3)]
            return Location(room, int(match.group(1)), (ord(match.group(2)) - ord('A'), roman))
        match = re.search(r"N/A|FALSE", seat)
        if match:
            return UNKNOWN
        match = re.search(r"(Front|Desk).*", seat)
        if match:
            return UNKNOWN # TODO handle these better
        raise RuntimeError(seat)
    def __repr__(self):
        return "Location(room={!r}, row={!r}, column={!r})".format(self.room, self.row, self.column)
    def __lt__(self, other):
        if isinstance(other, UnknownLocation):
            return False
        return (self.room, self.row, self.column) < (other.room, other.row, other.column)
    def __eq__(self, other):
        return not self < other and not other < self
    @property
    def room(self):
        return self.__room
    @property
    def row(self):
        return self.__row
    @property
    def column(self):
        return self.__column
    @property
    def y_region(self):
        return self.row.y_region

@total_ordering
class UnknownLocation(AbstractLocation):
    """
    A location which is UNKNOWN
    """
    def __eq__(self, other):
        return not ((self < other) or (other < self))
    def __hash__(self):
        return 0
    def __lt__(self, other):
        if isinstance(other, UnknownLocation):
            return False
        return True
    def __repr__(self):
        return "UNKNOWN"
    @property
    def row(self):
        return UNKNOWN
    @property
    def column(self):
        return UNKNOWN
    @property
    def room(self):
        return UNKNOWN
    @property
    def y_region(self):
        return UNKNOWN
    def __bool__(self):
        return False
UNKNOWN = UnknownLocation()

def __read_seating_chart(seat_file):
    """
    Reads a seating chart from a file
    """
    with open(seat_file) as fil:
        data = list(csv.reader(fil))
    email_loc = data[0].index("Email Address")
    seat_loc = data[0].index("Seat")
    room_loc = data[0].index("Room")
    return [(x[email_loc], Location.create_location(x[room_loc], x[seat_loc])) for x in data[1:]]

def __normalize_columns_in_chart(seating_chart):
    """
    Converts tuple columns into single numbers. Sets up minima and maxima for each column and places
        everything into Column objects.
    """
    yield from [x for x in seating_chart if isinstance(x[1], UnknownLocation)]
    knowns = [x for x in seating_chart if not isinstance(x[1], UnknownLocation)]
    knowns.sort(key=lambda x: x[1])
    def _normal_rows(sorted_by_room):
        for _, grouped_items in groupby(sorted_by_room, key=lambda x: x[1].room):
            grouped_items = list(grouped_items)
            minimum = min([x[1].row for x in grouped_items])
            maximum = max([x[1].row for x in grouped_items])
            for email, loc in grouped_items:
                yield email, Location(loc.room, Row(loc.row, minimum, maximum), loc.column)
    for _, grouped_items in groupby(_normal_rows(knowns), key=lambda x: x[1].row_identifier):
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

def _get_seating_chart(seat_file):
    """
    Performs process of getting a seating chart from a file and normalizing the columns.
    """
    return dict(__normalize_columns_in_chart(__read_seating_chart(seat_file)))

def _get_direction_dictionary(chart):
    """
    Takes in a seating chart dictionary EMAIL -> LOCATION

    Returns a lookup table dictionary EMAIL -> DIRECTION -> EMAIL of the person in that direction.
    """
    ident = lambda c: c[1].row_identifier
    by_row = {x : tuple(y) for x, y in groupby(sorted(chart.items(), key=ident), key=ident)}
    direct = defaultdict(lambda: defaultdict(lambda: UNKNOWN))
    for email in chart:
        location = chart[email]
        row_id = location.row_identifier
        if row_id == (UNKNOWN, UNKNOWN):
            continue
        alternatives = by_row[row_id]
        col_to_search = location.column
        for in_row in alternatives:
            relation = in_row[1].column.relation(col_to_search)
            if relation.sideways:
                direct[email][relation.direction_for] = in_row[0]
        for y_direction in (1, -1):
            modified_row_id = (row_id[0], row_id[1].move(y_direction))
            if modified_row_id not in by_row:
                continue
            altern_row = by_row[modified_row_id]
            val = location.column.closest(x[1].column for x in altern_row)
            direct[email][Direction((0, y_direction))] = altern_row[val][0]
    return direct
