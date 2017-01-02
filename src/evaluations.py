"""
Module for reading and processing evaluations, which are the scores for individual questions.
"""
from os import system
from os import listdir
import csv

from constants import DATA_DIR

class GradedMidterm:
    def __init__(self, name, *evals):
        self.name = name
        self.scores = [x.score for x in evals]
        self.rubrics_per_question = [x.rubric_items for x in evals]
        self.adjustments = [x.adjustment for x in evals]
        self.comments = [x.comments for x in evals]
        self.graders = [x.grader for x in evals]
        self.evals = evals
    def __repr__(self):
        return "GradedMidterm(%r, %s)" % (self.name, ", ".join(repr(x) for x in self.evals))

class Evaluation:
    """
    A data structure used for representing an evaluation, or a set of scores for a particular
        individual on a particular exam.
    """
    def __init__(self, score, rubric_items, adjustment, comments, grader):
        self.score = score
        self.rubric_items = rubric_items
        self.adjustment = adjustment
        self.comments = comments
        self.grader = grader
    def __repr__(self):
        tupled = (self.score, self.rubric_items, self.adjustment, self.comments, self.grader)
        return ("Evaluation(" + ", ".join(["{}"] * 5) + ")").format(*(repr(x) for x in tupled))

RUBRIC_ITEMS = {'true' : 1, 'false' : 0}

def read_evaluation_csv(csv_file):
    """
    Reads in a CSV as an evaluation. Format specified by assertions.
    """
    with open(csv_file, 'r') as fil:
        csvlines = list(csv.reader(fil))
    header, *rows = csvlines
    assert header[1] == "Name" and header[4] == "Score" and header [-3:] == ["Adjustment","Comments","Grader"]
    for run_id, row in enumerate(rows):
        if len(row) == 0:
            break
        rubric_items = [RUBRIC_ITEMS[x] for x in row[5:-3]]
        adjustment = float(row[-3]) if row[-3] != '' else 0
        yield (run_id, row[1]), \
                Evaluation(float(row[4]), rubric_items, adjustment, row[-2], row[-1])

def proc_evaluations(evaluations):
    """
    Extracts the given zip file of evaluations and merges them all into a single dictionary from name
        and exam id to evaluation list.
    """
    extracted = DATA_DIR + '/extracted/'
    system("unzip {} -d {}".format(evaluations, extracted))
    loc = extracted + listdir(extracted)[0]
    evals = []
    keys = set()
    for fil in listdir(loc):
        current = dict(read_evaluation_csv(loc + "/" + fil))
        keys.update(current.keys())
        evals.append(current)
    merged = {}
    for key in keys:
        identity, name = key
        merged[identity] = GradedMidterm(name, *[x[key] for x in evals])
    system('rm -r {}'.format(extracted))
    return merged

