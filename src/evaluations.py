from os import system
from os import listdir
import csv

from tools import flatten

class Evaluation:
    def __init__(self, score, rubric_items, adjustment, comments, grader):
        self.score = score
        self.rubric_items = rubric_items
        self.adjustment = adjustment
        self.comments = comments
        self.grader = grader
    def __repr__(self):
        tupled = (self.score, self.rubric_items, self.adjustment, self.comments, self.grader)
        return ("Evaluation(" + ", ".join(["{}"] * 4) + ")").format(*(repr(x) for x in tupled))
    @staticmethod
    def merged(evals):
        evals = list(evals)
        return Evaluation(
            flatten(x.score for x in evals),
            flatten(x.rubric_items for x in evals),
            flatten(x.adjustment for x in evals),
            flatten(x.comments for x in evals),
            flatten(x.grader for x in evals))

RUBRIC_ITEMS = {'true' : 1, 'false' : 0}

def read_evaluation_csv(csv_file):
    with open(csv_file, 'r') as fil:
        csvlines = list(csv.reader(fil))
    _, *rows = csvlines
    for run_id, row in enumerate(rows):
        if len(row) == 0:
            break
        rubric_items = [RUBRIC_ITEMS[x] for x in row[5:-3]]
        adjustment = float(row[-3]) if row[-3] != '' else 0
        yield (run_id, row[1]), \
                Evaluation([float(row[4])], rubric_items, [adjustment], [row[-2]], [row[-1]])

def proc_evaluations(evaluations):
    system("unzip {0} -d extracted".format(evaluations))
    loc = 'extracted/' + listdir('extracted')[0]
    evals = []
    keys = set()
    for fil in listdir(loc):
        current = dict(read_evaluation_csv(loc + "/" + fil))
        keys.update(current.keys())
        evals.append(current)
    merged = {}
    for key in keys:
        merged[key] = Evaluation.merged(x[key] for x in evals)
    system('rm -r extracted')
    return merged

