"""
A module containing a variety of methods for reporting
"""
from math import sqrt

from matplotlib import pyplot as plt
import numpy as np

from analytics import compensate_for_grader_means, all_pairs
from constants import DATA_DIR
from evaluations import proc_evaluations
from seating_chart import UNKNOWN, SeatingChart
from statistics import permutation_test, Partition
from tools import TempParams
from tools import show_or_save
from graphics import TerminalProgressBar
from models import ScoreIndependentModel

def grader_comparison_report():
    """
    Generates all the images necessary for the grader comparison report.
    """
    evals = proc_evaluations('%s/real-data/Midterm_1_evaluations.zip' % DATA_DIR)
    seats = SeatingChart('%s/real-data/mt1_seats.csv' % DATA_DIR)
    zero_meaned = compensate_for_grader_means(evals)
    create_grader_report(evals, "Midterm 1", q_filter=lambda x: x == 1.3,
                         path="report/img/grader-comparison.png", highlight={5 : "blue", 8 : "red"})
    by_room_chart(evals, seats, "Midterm 1", path="report/img/room-comparison.png")
    by_region_chart(evals, seats, "Midterm 1", path="report/img/region-comparison.png")
    permutation_test_of_pairs(lambda x: x.correlation, "Correlation", zero_meaned, seats,
                              TerminalProgressBar,
                              path="report/img/permutation-test-correlation.png")
    permutation_test_of_pairs(lambda x: x.abs_score_diff, "Absolute Score Difference",
                              zero_meaned, seats,
                              TerminalProgressBar,
                              path="report/img/permutation-test-abs-difference.png")
    score_indepenent_hist(evals, seats, path="report/img/score-indepenent-not-working.png")

def score_indepenent_hist(evals, seats, path):
    plt.figure()
    sim = ScoreIndependentModel(evals).create_grades(seats)
    plt.hist([evals.evaluation_for(x).score for x in evals.emails], color="red", alpha=0.4, label="Actual Data")
    plt.hist([sim.evaluation_for(x).score for x in sim.emails], color="blue", alpha=0.4, label="Score Independent Model")
    lgd = plt.legend(bbox_to_anchor=(1.5, 1))
    plt.xlabel("Score")
    plt.ylabel("Frequency")
    plt.title("Score Independent Model Scores vs. Real Scores")
    show_or_save(path, lgd)

def permutation_test_of_pairs(statistic, name, zero_meaned, seats, progress, path=None): #pylint: disable=C0103
    """
    Runs a permutation test on the differences between means of the given statistic in the adjacent
        and non-adjacent pairs of students
    """
    non_time_adjacents = list(pair
                              for pair in all_pairs(zero_meaned, seats, 2, progress)
                              if pair.are_same_room and not pair.are_time_adjacent)
    plt.figure()
    report = permutation_test(
        partition=Partition.partition(non_time_adjacents, lambda x: x.are_space_adjacent),
        summary=lambda x, y: np.mean(
            [statistic(u) for u in x]) - np.mean([statistic(u) for u in y]),
        progress=progress,
        number=100)
    report.report(
        summary_name="Difference in Mean %s Between Adjacent and Non-Adjacent Group" % name,
        title="N=%s" % (len(zero_meaned.emails)), path=path)

def create_grader_report(evals, exam_name, q_filter=lambda _: True, path=None, highlight=None):
    """
    Creates a report on grader anomalies for a given set of evaluations
    """
    def _color(index):
        if highlight is not None and index not in highlight:
            return "black"
        else:
            return highlight[index]
    for question_name, ques in evals:
        if not q_filter(question_name):
            continue
        plt.figure(figsize=(15, 3))
        plt.subplot(121)
        maximum = max([ques.score_for(x).complete_score.score for x in ques.emails])
        def _all_graders():
            # pylint: disable=W0640
            for grader in sorted(ques.graders):
                question = ques.for_grader(grader)
                count = len(list(question.emails))
                if count < 20:
                    continue
                yield question.mean_score, question.std_score * 1.96 / sqrt(count)
        means_stds = list(_all_graders())
        for index, mean_std in enumerate(means_stds):
            mean, std = mean_std
            plt.errorbar([index + 1], [mean.score], yerr=[std.score],
                         color=_color(index + 1), label="95% CI", fmt="*")
        plt.xlim(0.5, len(means_stds) + 0.5)
        plt.title("Average score by grader for Midterm 1, Problem %s" % question_name)
        plt.ylabel("Points")
        plt.xlabel("Grader #")
        plt.ylim(0, maximum)
        plt.subplot(122)
        xvals = list(range(len(means_stds[0][0].rubric_items)))
        for index, mean_std in enumerate(means_stds):
            mean, std = mean_std
            plt.errorbar(np.array(xvals) + 1,
                         100 * np.array(mean.rubric_items),
                         yerr=100 * np.array(std.rubric_items),
                         fmt='-', label="Grader #%s" % (index + 1),
                         color=_color(index + 1))
        plt.xlim(xvals[0] + 0.5, xvals[-1] + 1.5)
        lgd = plt.legend(bbox_to_anchor=(1.4, 1))
        plt.gca().set_xticks(np.array(xvals) + 1)
        plt.title("Per Rubric Item for %s, Problem %s" % (exam_name, question_name))
        plt.ylabel("Percentage Selected")
        plt.xlabel("Rubric Item Number")
        show_or_save(path, lgd)

def draw_exam_profiles(categories, exam_name, cat_type, path):
    """
    Gets a chart of every room's exam profile.
    """
    with TempParams(18):
        plt.figure(figsize=(15, 5))
        for name, for_cat in categories:
            if not isinstance(name, str):
                continue
            mean = 100 * np.mean(for_cat, axis=0)
            std = 100 * np.std(for_cat, axis=0) / sqrt(len(mean)) * 1.96
            plt.errorbar(np.arange(len(mean)), mean, yerr=std, label=name, fmt='-')
        lgd = plt.legend(bbox_to_anchor=(1.25, 1))
        plt.ylim(-5, 105)
        plt.xlim(-1, len(mean))
        plt.xlabel("Rubric Item (ordered by position on the exam)")
        plt.ylabel("% Students With Rubric Item (95% CI)")
        plt.title("%s Exam Profiles By %s" % (exam_name, cat_type))
        show_or_save(path, lgd)

def by_region_chart(evals, seats, exam_name, path=None):
    """
    Produce an exam profile chart of each sector of the room (Front/Middle/Back).
    """
    by_room_position = {x : [] for x in ("front", "middle", "back")}
    for email in evals.emails:
        if email not in seats.emails:
            continue
        region = seats.y_region(email)
        if region == UNKNOWN:
            continue
        by_room_position[region].append(evals.exam_profile(email))
    draw_exam_profiles(by_room_position.items(), exam_name, "Region", path)

def by_room_chart(evals, seats, exam_name, path=None):
    """
    Gets a chart of every room's exam profile.
    """
    categories = []
    for room, for_room in evals.by_room(seats):
        average = []
        for email in for_room.emails:
            average.append([x for x in for_room.exam_profile(email)])
        categories.append((room, average))
    draw_exam_profiles(categories, exam_name, "Room", path)

if __name__ == '__main__':
    grader_comparison_report()
