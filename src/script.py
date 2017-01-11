"""
A script to be run.
"""
from models import plausible_parameters, binary_cheater, score_diff_summary, RandomSeatingModel
from graphics import TerminalProgressBar

from evaluations import proc_evaluations
from seating_chart import SeatingChart
from constants import DATA_DIR

EVALS = proc_evaluations('%s/real-data/Midterm_1_evaluations.zip' % DATA_DIR)
SEATS = SeatingChart('%s/real-data/mt1_seats.csv' % DATA_DIR)

for result in plausible_parameters(EVALS, SEATS,
                                   binary_cheater(RandomSeatingModel, ()),
                                   score_diff_summary, 1000, 200, TerminalProgressBar):
    print(result)
