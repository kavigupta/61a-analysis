"""
A module for handling models.
"""

from abc import abstractmethod, ABCMeta
from math import floor
import numpy as np
from numpy.random import random, choice, normal, shuffle

from statistics import p_value, PermutationReport, TailType
from analytics import all_pairs, compensate_for_grader_means
from graphics import NoProgressBar

from constants import ALL_WAYS

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
        yield model_on_params(true_grades, true_seats, true_value, model, params, summary, n_trials)

def model_on_params(true_grades, true_seats, true_value, model, params, summary, n_trials):
    """
    Run the given model on the given parameters.

    Inputs:
        true_grades: ExamGrades
            the actual grade distribution for the course
        true_seats: SeatingChart
            the actual seating chart for the course
        true_value:
            the result of calling `summary(true_grades, true_seats)` (for the purpose of efficiency
                over repeated calls)
        model: Class extending Model
            which is of interest
        params: paramtype(model)
            the parameters to plug into the model
        summary: (ExamGrades, SeatingChart) -> Float
            which we are testing
        granularity: Integer
            the number of parameter values to try

    Output:
        (parameter, probability, report). see plausible_parameters for more info
    """
    current_model = model(true_grades, *params)
    model_values = [summary(current_model.create_grades(true_seats),
                            true_seats)
                    for _ in range(n_trials)]
    p_val = p_value(true_value, model_values, TailType.UNKNOWN)
    return params, p_val, PermutationReport(true_value, model_values, p_val)

def score_diff_summary(grades, seats):
    """
    A summary statistic representing the difference in mean absolute score difference between the
        adjacent and non-adjacent groups of pairs of students.
    """
    zero_meaned = compensate_for_grader_means(grades)
    non_time_adjacents = all_pairs(zero_meaned, seats, 2, NoProgressBar,
                                   require_same_room=True, require_not_time_adj=True,
                                   adjacency_type=ALL_WAYS)
    space_adj = []
    non_space_adj = []
    for pair in non_time_adjacents:
        if pair.are_space_adjacent:
            space_adj.append(pair.abs_score_diff)
        else:
            non_space_adj.append(pair.abs_score_diff)
    return np.mean(space_adj) - np.mean(non_space_adj)

class PointEvaluation:
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

class QuestionIndependentModel(Model):
    """
    A simple model where every question is assumed to be independent
    """
    def __init__(self, environment):
        super().__init__(environment)
        self.__mean_stds = []
        for _, question in environment:
            self.__mean_stds.append((question.mean_score.score, question.std_score.score))
    def _get_grades(self, _):
        for email in self._environment.emails:
            yield email, PointEvaluation([normal(m, s) for m, s in self.__mean_stds])
    @staticmethod
    def parameters(_):
        return [()]
    @staticmethod
    def name():
        return "Question Independent Model"

class RandomSeatingModel(Model):
    """
    Randomly assigns students to seats.
    """
    def _get_grades(self, _):
        evals = [self._environment.evaluation_for(email) for email in self._environment.emails]
        shuffle(evals)
        for evalu, email in zip(evals, self._environment.emails):
            yield email, PointEvaluation([x.total_score for x in evalu.evals])
    @staticmethod
    def parameters(_):
        return [()]
    @staticmethod
    def name():
        return "Random Seating Model"
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
            self.__n_cheaters = int(round(len(environment.emails) * percent_cheaters))
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
            yield 0, 0
            granularity -= 1
            if granularity == 0:
                return
            n_pc = floor(granularity ** (2/3))
            n_k = granularity // n_pc
            for percent_cheaters in np.linspace(0, 1, n_pc + 1)[1:]:
                for percent_cheating in np.linspace(0, 1, n_k + 1)[1:]:
                    yield percent_cheaters, percent_cheating
        @staticmethod
        def name():
            return "Binary Cheater Model [based on %s]" % base_model_type.name()
    return BinaryCheaterModel
