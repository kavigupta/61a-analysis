"""
A script to be run.
"""
from models import plausible_parameters, binary_cheater, score_diff_summary, RandomSeatingModel
from graphics import TerminalProgressBar

from evaluations import proc_evaluations
from seating_chart import SeatingChart

EVALS = proc_evaluations('/home/kavi/data/real-data/Midterm_1_evaluations.zip')
SEATS = SeatingChart('/home/kavi/data/real-data/mt1_seats.csv')

for result in plausible_parameters(EVALS, SEATS,
                                   binary_cheater(RandomSeatingModel, ()),
                                   score_diff_summary, 1000, 200, TerminalProgressBar):
    print(result)
