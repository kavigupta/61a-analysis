"""
A module for handling models.
"""

from abc import abstractmethod, ABCMeta
from math import floor
import numpy as np
from numpy.random import random, choice

from statistics import p_value, Partition, PermutationReport
from analytics import all_pairs, compensate_for_grader_means
from graphics import NoProgressBar

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
    @staticmethod
    @abstractmethod
    def name():
        """
        The model's name.
        """
        pass

def plausible_parameters(true_grades, true_seats, model, summary, granularity, n_trials, progress):
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
    p_bar = progress(granularity)
    for index, params in enumerate(model.parameters(granularity)):
        p_bar.update(index)
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
                              for pair in all_pairs(zero_meaned, seats, 2, NoProgressBar)
                              if pair.are_same_room and not pair.are_time_adjacent)
    parts = Partition.partition(non_time_adjacents, lambda x: x.are_space_adjacent)
    return np.mean([x.abs_score_diff for x in parts.group_a]) \
                - np.mean([x.abs_score_diff for x in parts.group_b])

class PointEvaluation: # pylint: disable=R0903
    """
    Represents a Mock Evaluation with each point being an independent item
    """
    means_need_compensation = False
    def __init__(self, points):
        self.points = points
        self.score = None
        self.recalculate_grade()
    def recalculate_grade(self):
        """
        Recalculate the grade as the sum of the points. Necessary if an external source messes with
            the points.
        """
        self.score = sum(self.points)

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
    @staticmethod
    def name():
        return "Score Independent Model"


def binary_cheater(base_model_type, params):
    """
    Takes a baseline PointEvaluation-generating model and makes some of the people cheaters.

    Inputs:
        base_model_type: the type of model to use by default.
        params: the parameters to shove into the baseline model.
    """
    #TODO params be generated rather than taken as arguments
    class BinaryCheaterModel(Model):
        """
        A model with two parameters that accounts for cheaters.

        Parameters:
            percent_cheaters: the ratio of students who cheat
            ratio_cheating: the fraction of exam parts / points they cheat on
        """
        def __init__(self, environment, percent_cheaters, ratio_cheating):
            super().__init__(environment)
            self.__n_cheaters = round(len(environment.emails) * percent_cheaters)
            self.__ratio_cheating = ratio_cheating
            self.__base_model = base_model_type(environment, *params)
        def _get_grades(self, seats):
            grades = dict(self.__base_model._get_grades(seats)) # pylint: disable=W0212
            cheaters = choice(list(grades), size=self.__n_cheaters, replace=False)
            for cheat in cheaters:
                if cheat not in grades:
                    continue
                marks = list(x for x in seats.adjacent_to(cheat) if x in grades)
                if len(marks) == 0:
                    continue
                mark = choice(marks)
                indices = choice(len(grades[cheat].points),
                                 floor(self.__ratio_cheating * len(grades[cheat].points)))
                if len(indices) == 0:
                    continue
                for index in indices:
                    grades[cheat].points[index] = grades[mark].points[index]
                grades[cheat].recalculate_grade()
            return grades.items()
        @staticmethod
        def parameters(granularity):
            n_pc = floor(granularity ** (2/3))
            n_k = granularity // n_pc
            for percent_cheaters in np.linspace(0, 1, n_pc):
                for percent_cheating in np.linspace(0, 1, n_k):
                    yield percent_cheaters, percent_cheating
        @staticmethod
        def name():
            return "Binary Cheater Model [based on %s]" % base_model_type.name()
    return BinaryCheaterModel
