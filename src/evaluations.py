"""
Module for reading and processing evaluations, which are the scores for individual questions.
"""
from os import system
from os import listdir
import csv

import numpy as np

from graded_exam import ExamGrades

from constants import DATA_DIR

class Evaluation:
    """
    A set of questions for a given individual
    """
    def __init__(self, name, email, *evals):
        self.name = name
        self.email = email
        self.evals = evals
    def __repr__(self):
        evaluations = ", ".join(repr(x) for x in self.evals)
        return "Evaluation(%r, %r, %s)" % (self.name, self.email, evaluations)
    def zero_mean(self, means):
        """
        Subtract out the given means : iterable of (score, rubric, adjustment) from each scored
            question.
        """
        return Evaluation(self.name, self.email,
                          *[x.zero_mean(y) for x, y in zip(self.evals, means)])
    @property
    def __norm_vec(self):
        all_rubrics = np.array([y for x in self.evals for y in x.rubric_items])
        return all_rubrics / np.linalg.norm(all_rubrics)
    def correlation(self, other):
        """
        Find the correlation of this and another evaluation
        """
        return np.sum(self.__norm_vec * other.__norm_vec) # pylint: disable=W0212

class ScoredQuestion:
    """
    A data structure used for representing an evaluation, or a set of scores for a particular
        individual on a particular exam.
    """
    def __init__(self, email, score, rubric_items, adjustment, comments, grader):
        self.email = email
        self.score = score
        self.rubric_items = rubric_items
        self.adjustment = adjustment
        self.comments = comments
        self.grader = grader
    def __repr__(self):
        tupled = (self.score, self.email,
                  self.rubric_items, self.adjustment,
                  self.comments, self.grader)
        return ("ScoredQuestion(" + ", ".join(["{!r}"] * 6) + ")").format(*tupled)
    def zero_mean(self, mean):
        """
        Removed the score in each case.
        """
        m_score, m_rubric, m_adj = mean
        return ScoredQuestion(
            self.email,
            self.score - m_score,
            [x - y for x, y in zip(self.rubric_items, m_rubric)],
            self.adjustment - m_adj,
            self.comments,
            self.grader)

RUBRIC_ITEMS = {'true' : 1, 'false' : 0}

def read_evaluation_csv(csv_file):
    """
    Reads in a CSV as an evaluation. Format specified by assertions.
    """
    with open(csv_file, 'r') as fil:
        csvlines = list(csv.reader(fil))
    header, *rows = csvlines
    assert header[1] == "Name"
    assert header[3] == "Email"
    assert header[4] == "Score"
    assert header[-3:] == ["Adjustment", "Comments", "Grader"]
    for run_id, row in enumerate(rows):
        if len(row) == 0:
            break
        rubric_items = [RUBRIC_ITEMS[x] for x in row[5:-3]]
        adjustment = float(row[-3]) if row[-3] != '' else 0
        yield (run_id, row[1], row[3]), \
                ScoredQuestion(row[3], float(row[4]), rubric_items, adjustment, row[-2], row[-1])


def proc_evaluations(evaluations):
    """
    Extracts the given zip file of evaluations and merges them all into a single dictionary from
        name and exam id to evaluation list.
    """
    extracted = DATA_DIR + '/extracted/'
    system("unzip {} -d {}".format(evaluations, extracted))
    loc = extracted + listdir(extracted)[0]
    evals = []
    keys = set()
    for fil in listdir(loc):
        problem = float(fil[:fil.index("_")])
        current = dict(read_evaluation_csv(loc + "/" + fil))
        keys.update(current.keys())
        evals.append((problem, current))
    evals.sort()
    problems = [x for x, _ in evals]
    merged = {}
    for key in keys:
        identity, name, email = key
        merged[identity] = Evaluation(name, email, *[x[key] for _, x in evals])
    system('rm -r {}'.format(extracted))
    return ExamGrades.create(problems, merged)

