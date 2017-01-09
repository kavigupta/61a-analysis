"""
A module for handling models.
"""

from abc import abstractmethod

from statistics import p_value

class Model(meta=ABCMeta):
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
