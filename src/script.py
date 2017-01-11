
from models import plausible_parameters, binary_cheater, score_diff_summary, RandomSeatingModel
from graphics import TerminalProgressBar

from evaluations import proc_evaluations
from seating_chart import SeatingChart

evals = proc_evaluations('/home/kavi/data/real-data/Midterm_1_evaluations.zip')
seats = SeatingChart('/home/kavi/data/real-data/mt1_seats.csv')

params = list(plausible_parameters(evals, seats,
                              binary_cheater(RandomSeatingModel, ()),
                              score_diff_summary, 64, 60, TerminalProgressBar))
print("\n ANSWER FOLLOWS:")
print(params)
