"""
A script to be run.
"""
from sys import argv
from multiprocessing import Pool

from models import model_on_params, binary_cheater, score_diff_summary, RandomSeatingModel

from evaluations import proc_evaluations
from seating_chart import SeatingChart
from constants import DATA_DIR

def usage():
    """
    Print out a usage statement
    """
    raise RuntimeError("Usage: script.py GRANULARITY N_TRIALS N_THREADS")

if len(argv) != 4:
    usage()

try:
    GRANULARITY = int(argv[1])
    N_TRIALS = int(argv[2])
    N_THREADS = int(argv[3])
except ValueError:
    usage()

EVALS = proc_evaluations('%s/real-data/Midterm_1_evaluations.zip' % DATA_DIR)
SEATS = SeatingChart('%s/real-data/mt1_seats.csv' % DATA_DIR)

MODEL = binary_cheater(RandomSeatingModel, ())

TRUE_VALUE = score_diff_summary(EVALS, SEATS)

PARAMS = list(MODEL.parameters(GRANULARITY))
def proc_param(param):
    """
    Process the given parameter
    """
    result = model_on_params(EVALS, SEATS, TRUE_VALUE, MODEL, param, score_diff_summary, N_TRIALS)
    print(result)

Pool(N_THREADS).map(proc_param, PARAMS)
