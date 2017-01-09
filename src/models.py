"""
A module for handling models.
"""

from abc import abstractmethod, ABCMeta
import numpy as np
from numpy.random import random

from statistics import p_value, Partition, PermutationReport
from analytics import all_pairs, compensate_for_grader_means

class Model(metaclass=ABCMeta):
    """
    Represents the abstract concept of a model, which has a parameter and a way to generate grades.
    """
    def __init__(self, environment):
        self._environment = environment
    def create_grades(self, seating_chart):
        """
        Creates an ExamGrades at random for the given seating chart.
        """
        return self._environment.change_grades(dict(self._get_grades(seating_chart)))
    @abstractmethod
    def _get_grades(self, seating_chart):
        """
        Randomly generates a generator (email, Evaluation) for the given exam.
        """
        pass
    @staticmethod
    @abstractmethod
    def parameters(granularity):
        """
        Gets a set of parameters to run the model under.

        granularity: the number of parameters to generate.
        """
        pass

def plausible_parameters(true_grades, true_seats, model, summary, granularity, n_trials):
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
    for params in model.parameters(granularity):
        current_model = model(true_grades, *params)
        model_values = []
        for _ in range(n_trials):
            model_grades = current_model.create_grades(true_seats)
            model_values.append(summary(model_grades, true_seats))
        p_val = p_value(true_value, model_values)
        yield params, p_val, PermutationReport(true_value, model_values, p_val)

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

class PointEvaluation:
    means_need_compensation = False
    """
    Represents a Mock Evaluation with each point being an independent item
    """
    def __init__(self, points):
        self.score = sum(points)
        self.points = points

class ScoreIndependentModel(Model):
    """
    A simple model where every point is assumed to be independent of every other point.
    """
    def __init__(self, environment):
        super().__init__(environment)
        self.__n_questions = round(environment.max_score)
        self.__p = environment.mean_score / self.__n_questions
    def _get_grades(self, _):
        for email in self._environment.emails:
            yield email, PointEvaluation([random() < self.__p for _ in range(self.__n_questions)])
    @staticmethod
    def parameters(_):
        return [()]
