"""
A script to be run.
"""
from sys import argv
from multiprocessing import Pool

from statistics import TailType

from models import model_on_params, binary_cheater, one_way_vs_two_way_summary, RandomSeatingModel

from evaluations import proc_evaluations
from seating_chart import AdjacencyType, SeatingChart
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

def one_way_vs_two_way_summary_correlation(grades, seats):
    """
    Produces differences in the correlations between one-apart and two-apart individuals.
    """
    return one_way_vs_two_way_summary(grades, seats,
                                      gambler_fallacy_allowable_limit=GAMBLER_FALLACY_ALLOWABLE_LIMIT,
                                      similarity_fn=lambda x, y: x.correlation(y))

GAMBLER_FALLACY_ALLOWABLE_LIMIT = 1

EVALS = proc_evaluations('%s/real-data/mt1_evaluations.zip' % DATA_DIR)
SEATS = SeatingChart('%s/real-data/mt1_seats.csv' % DATA_DIR)

MODEL = binary_cheater(RandomSeatingModel, (), AdjacencyType.sideways_only)

TRUE_VALUE = one_way_vs_two_way_summary_correlation(EVALS, SEATS)

PARAMS = list((cheaters, ratio) for cheaters, ratio in MODEL.parameters(GRANULARITY) if cheaters < 0.2)

def proc_param(param):
    """
    Process the given parameter
    """
    result = model_on_params(EVALS, SEATS, TRUE_VALUE, MODEL, param, one_way_vs_two_way_summary_correlation, N_TRIALS, tail_type=TailType.KNOWN_HIGH)
    print(result)

Pool(N_THREADS).map(proc_param, PARAMS)
