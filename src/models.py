"""
A module for handling models.
"""

from abc import abstractmethod, ABCMeta
import numpy as np

from statistics import p_value, Partition
from analytics import all_pairs, compensate_for_grader_means

class Model(metaclass=ABCMeta):
    """
    Represents the abstract concept of a model, which has a parameter and a way to generate grades.
    """
    def __init__(self, environment):
        self._environment = environment
    @abstractmethod
    def create_grades(self, seating_chart):
        """
        Creates a set of grades for the given seating chart.
        """
        pass
    @abstractmethod
    @staticmethod
    def parameters(granularity):
        """
        Gets a set of parameters to run the model under.

        granularity: the number of parameters to generate.
        """
        pass

def plausible_parameters(true_grades, true_seats, summary, model, granularity, n_trials):
    # pylint: disable=R0913
    """
    Inputs:
        true_grades: ExamGrades
            the actual grade distribution for the course
        true_seats: SeatingChart
            the actual seating chart for the course
        model: Class extending Model
            which is of interest
        summary: (ExamGrades, SeatingChart) -> Float
            which we are testing
        granularity: Integer
            the number of parameter values to try
    Output:
        a generator of (parameter, probability) for each parameter value we try. The probability is
            P[summary=given_summary | model(parameter) is true]
    """
    true_value = summary(true_grades, true_seats)
    for param in model.parameters(granularity):
        current_model = model(param)
        model_values = []
        for _ in range(n_trials):
            model_grades = current_model.create_grades(true_seats)
            model_values.append(summary(model_grades, true_seats))
        yield param, p_value(true_value, model_values)

def score_diff_summary(grades, seats):
    """
    A summary statistic representing the difference in mean absolute score difference between the
        adjacent and non-adjacent groups of pairs of students.
    """
    zero_meaned = compensate_for_grader_means(grades)
    non_time_adjacents = list(pair
                              for pair in all_pairs(zero_meaned, seats, 2)
                              if pair.are_same_room and not pair.are_time_adjacent)
    parts = Partition.partition(non_time_adjacents, lambda x: x.are_space_adjacent)
    return np.mean([x.abs_score_diff for x in parts.group_a]) \
                - np.mean([x.abs_score_diff for x in parts.group_b])