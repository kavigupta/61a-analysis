"""
A set of classes for handling graded exams
"""
from collections import defaultdict
import numpy as np

from tools import cached_property

class ExamQuestion:
    """
    A view on a particular question, with optional filtering
    """
    def __init__(self, exam_grades, problem, pred=lambda x: True):
        self.__exam_grades = exam_grades
        self.__problem = problem
        self.__pred = pred
    def __filter(self, new_pred):
        return ExamQuestion(self.__exam_grades, self.__problem,
                            lambda x: self.__pred(x) and new_pred(x))
    def for_grader(self, grader):
        """
        Filters on the given grader.
        """
        return self.__filter(lambda x: x.grader == grader)
    def score_for(self, email):
        """
        Return the score for the given EMAIL
        """
        return self.__exam_grades._question_score_for(self.__problem, email) # pylint: disable=W0212
    @property
    def evaluations(self):
        """
        Return a list of all evaluations
        """
        return (x for x in self.__exam_grades.question_scores_for(self.__problem) if self.__pred(x))
    @property
    def graders(self):
        """
        Return a list of all graders
        """
        return set(x.grader for x in self.evaluations)
    @property
    def __scores(self):
        return [x.complete_score for x in self.evaluations]
    @property
    def std_score(self):
        """
        Get the standard deviation of the rubrics
        """
        return np.std(self.__scores)
    @property
    def mean_score(self):
        """
        Get the mean of the rubrics
        """
        return np.mean(self.__scores)
    @property
    def emails(self):
        """
        Get a list of emails in our evaluations
        """
        return (x.email for x in self.evaluations)

class ExamGrades:
    """
    A list of all exam grades for a given exam.
    """
    def __init__(self, problem_names, location_per_email, evaluation_per_email):
        self.__problem_names = problem_names
        self.__location_per_email = location_per_email
        self.__evaluation_per_email = evaluation_per_email
        self.__emails = set(evaluation_per_email.keys())
    def by_room(self, seating_chart):
        """
        Input: seating chart
        Output: iterable of room name, grades with only emails in that room
        """
        by_room = defaultdict(lambda: [])
        for email in seating_chart.emails:
            if email not in self.emails:
                continue
            current = email, self.__location_per_email[email], self.__evaluation_per_email[email]
            by_room[seating_chart.room_for(email)].append(current)
        for room, items in by_room.items():
            yield room, ExamGrades(self.__problem_names,
                                   {e : l for e, l, _ in items}, {e : ev for e, _, ev in items})
    def exam_profile(self, email):
        """
        Returns the exam profile, a list of every rubric item possible.
        """
        return [x
                for ev in self.evaluation_for(email).evals
                for x in ev.complete_score.rubric_items]
    def change_grades(self, new_evals_per_email):
        """
        Outputs a new ExamGrades object with the given evaluations per email dictionary.
        """
        return ExamGrades(self.__problem_names, self.__location_per_email, new_evals_per_email)
    @cached_property
    def max_score(self):
        """
        Outputs the maximum score any student acheived on this exam
        """
        return max(x.score for x in self.__evaluation_per_email.values())
    @cached_property
    def mean_score(self):
        """
        Outputs the mean score any student acheived on this exam
        """
        return np.mean([x.score for x in self.__evaluation_per_email.values()])
    @staticmethod
    def create(problem_names, grades_per_index):
        """
        Create a given exam grades dictionary from
            problem_names: a list of problem names.
            grades_per_index: a dictionary : TimeIndex -> Evaluation
        """
        location_per_email = {e.email : i for i, e in grades_per_index.items()}
        evaluation_per_email = {e.email : e for i, e in grades_per_index.items()}
        return ExamGrades(problem_names, location_per_email, evaluation_per_email)
    def __iter__(self):
        return iter((name, ExamQuestion(self, name)) for name in self.__problem_names)
    def question_scores_for(self, problem):
        """
        Get the question scores for the given problem.
        """
        p_index = self.__problem_names.index(problem)
        for full_grade in self.__evaluation_per_email.values():
            yield full_grade.evals[p_index]
    def _question_score_for(self, problem, email):
        """
        Get the question scores for the given problem.
        """
        p_index = self.__problem_names.index(problem)
        return self.evaluation_for(email).evals[p_index]

    @property
    def emails(self):
        """
        Get a set of emails of students who took this exam
        """
        return self.__emails
    def evaluation_for(self, email):
        """
        Get the evaluation mapped to the given email.
        """
        return self.__evaluation_per_email[email]
    def remove(self, emails):
        """
        Returns a new ExamGrades object with the given iterable of emails filtered out.
        """
        return ExamGrades(
            self.__problem_names,
            {x : y for x, y in self.__location_per_email.items() if x not in emails},
            {x : y for x, y in self.__evaluation_per_email.items() if x not in emails})
    def __replace(self, updater):
        return ExamGrades(
            self.__problem_names,
            self.__location_per_email,
            {x : updater(y) for x, y in self.__evaluation_per_email.items()})
    def zero_meaned(self):
        """
        Zero means each question score by grader.
        """
        def mean_per_question_and_grader():
            """
            Produces an iterable of
                keys : question and grader
                values : the mean score, rubric items, and adjustment
            """
            for quest, grades in self:
                for grader in grades.graders:
                    by_grader = grades.for_grader(grader)
                    yield ((quest, grader), by_grader.mean_score)
        mpqag = dict(mean_per_question_and_grader())
        def updater(elem):
            """
            Takes an evaluation and zero means it.
            """
            def means():
                """
                Returns the means for each question for the given grader.
                """
                for que, eva in zip(self.__problem_names, elem.evals):
                    yield mpqag[(que, eva.grader)]
            return elem.zero_mean(means())
        return self.__replace(updater)
    def time_diff(self, email_a, email_b):
        """
        Get the difference between the times at which email_a and email_b were processed (in number
            of exams).
        """
        return self.__location_per_email[email_a] - self.__location_per_email[email_b]
