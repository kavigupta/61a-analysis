
from models import plausible_parameters, RandomSeatingModel, binary_cheater, score_diff_summary
from graphics import TerminalProgressBar
from evaluations import proc_evaluations
from seating_chart import SeatingChart
from constants import DATA_DIR

from sys import argv

def main(arg):
    evals = proc_evaluations('%s/real-data/Midterm_1_evaluations.zip' % DATA_DIR)
    seats = SeatingChart('%s/real-data/mt1_seats.csv' % DATA_DIR)
    if arg == "--plausible-params":
        profile_plausible_params(evals, seats)
    else:
        raise RuntimeError("Argument %s not recognized" % arg)


def profile_plausible_params(evals, seats):
    list(plausible_parameters(evals, seats,
                                  binary_cheater(RandomSeatingModel, ()),
                                  score_diff_summary, 1, 10, TerminalProgressBar))

if __name__ == '__main__':
    main(argv[1])
