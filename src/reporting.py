"""
A module containing a variety of methods for reporting
"""
from math import sqrt

from collections import OrderedDict

from matplotlib import pyplot as plt
import numpy as np

from analytics import compensate_for_grader_means, all_pairs
from constants import DATA_DIR
from evaluations import proc_evaluations
from seating_chart import UNKNOWN, SeatingChart, AdjacencyType
from statistics import permutation_test, Partition, Bootstrap, matched_differences_bootstrap
from tools import TempParams
from tools import show_or_save
from models import ScoreIndependentModel, QuestionIndependentModel

def load_all():
    """
    Return evaluations, seats, and zero_meaned evaluations from each of the results.
    """
    evals = OrderedDict()
    seats = OrderedDict()
    zero_meaneds = OrderedDict()
    zero_meaned_no_correction = OrderedDict()
    for exam in "mt1", "mt2", "final":
        evals[exam] = proc_evaluations('%s/real-data/%s_evaluations.zip' % (DATA_DIR, exam))
        seats[exam] = SeatingChart('%s/real-data/%s_seats.csv' % (DATA_DIR, exam))
        zero_meaneds[exam] = compensate_for_grader_means(evals[exam])
        zero_meaned_no_correction[exam] = compensate_for_grader_means(evals[exam],
                                                                      z_thresh=float('inf'))
    return evals, seats, zero_meaneds, zero_meaned_no_correction

def grader_comparison_report():
    """
    Generates all the images necessary for the grader comparison report.
    """
    evals, seats, zero_meaneds, zero_meaned_no_correction = load_all()
    create_grader_report(evals["mt1"], "Midterm 1", q_filter=lambda x: x == 1.3,
                         path="report/img/grader-comparison.png", highlight={5 : "blue", 8 : "red"})
    by_room_chart(evals["mt1"], seats["mt1"], "Midterm 1", path="report/img/room-comparison.png")
    by_region_chart(evals["mt1"], seats["mt1"], "Midterm 1",
                    path="report/img/region-comparison.png")
    plt.figure(figsize=(10, 5))
    matched_difference_graph(zero_meaneds, seats, list(range(3)),
                             lambda x, y: x.correlation(y), "rubric-item-level correlation",
                             path="report/img/matched-diff-rubric-correlation.png")
    plt.figure(figsize=(10, 5))
    matched_difference_graph(zero_meaned_no_correction, seats, list(range(3)),
                             lambda x, y: -abs(x.score - y.score),
                             "negative absolute score difference",
                             path="report/img/matched-diff-negative-abs-score-diff.png")
    model_grades_hist((ScoreIndependentModel, QuestionIndependentModel),
                      evals["mt1"], seats["mt2"], path="report/img/independents-not-working.png")

def model_grades_hist(models, evals, seats, path):
    """
    Show the histogram for the score-independent and actual models.
    """
    colors = ["red", "blue", "green"] * len(models)
    plt.figure()
    plt.hist([evals.evaluation_for(x).score for x in evals.emails],
             color="white", alpha=0.4, label="Actual Data")
    for model, color in zip(models, colors):
        sim = model(evals).create_grades(seats)
        plt.hist([sim.evaluation_for(x).score for x in sim.emails],
                 color=color, alpha=0.4, label=model.name())
    lgd = plt.legend(bbox_to_anchor=(1.5, 1))
    plt.xlabel("Score")
    plt.ylabel("Frequency")
    plt.title("Model Scores Comparison")
    show_or_save(path, lgd)

def permutation_test_of_pairs(statistic, name, zero_meaned, seats, progress, adjacency_type,
                              path=None, number=100):
    """
    Runs a permutation test on the differences between means of the given statistic in the adjacent
        and non-adjacent pairs of students
    """
    non_time_adjacents = list(all_pairs(zero_meaned, seats, 2, progress,
                                        require_same_room=True, require_not_time_adj=True,
                                        adjacency_type=adjacency_type))
    plt.figure(figsize=(8, 3))
    report = permutation_test(
        partition=Partition.partition(non_time_adjacents, lambda x: x.are_space_adjacent),
        summary=lambda x, y: np.mean(
            [statistic(u) for u in x]) - np.mean([statistic(u) for u in y]),
        progress=progress,
        number=number)
    report.report(
        summary_name="Difference in Mean %s Between Adjacent and Non-Adjacent Group" % name,
        title="N=%s" % (len(zero_meaned.emails)), path=path)
    return report.p_value

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
        _report_for_question(ques, _color, exam_name, question_name, path)

def _report_for_question(ques, color, exam_name, question_name, path):
    def _all_graders():
        # pylint: disable=W0640
        for grader in sorted(ques.graders):
            question = ques.for_grader(grader)
            count = len(list(question.emails))
            if count < 20:
                continue
            yield question.mean_score, question.std_score * 1.96 / sqrt(count)
    def _bottom_plot():
        xvals = list(range(len(means_stds[0][0].rubric_items)))
        for index, mean_std in enumerate(means_stds):
            mean, std = mean_std
            plt.errorbar(np.array(xvals) + 1,
                         100 * np.array(mean.rubric_items),
                         yerr=100 * np.array(std.rubric_items),
                         fmt='-', label="Grader #%s" % (index + 1),
                         color=color(index + 1))
        plt.xlim(xvals[0] + 0.5, xvals[-1] + 1.5)
        lgd = plt.legend(bbox_to_anchor=(1.4, 1))
        plt.gca().set_xticks(np.array(xvals) + 1)
        plt.title("Per Rubric Item for %s, Problem %s" % (exam_name, question_name))
        plt.ylabel("Percentage Selected")
        plt.xlabel("Rubric Item Number")
        show_or_save(path, lgd)
    def _top_plot():
        for index, mean_std in enumerate(means_stds):
            mean, std = mean_std
            plt.errorbar([index + 1], [mean.score], yerr=[std.score],
                         color=color(index + 1), label="95% CI", fmt="*")
        plt.xlim(0.5, len(means_stds) + 0.5)
        plt.title("Average score by grader for Midterm 1, Problem %s" % question_name)
        plt.ylabel("Points")
        plt.xlabel("Grader #")
        plt.ylim(0, maximum)
    means_stds = list(_all_graders())
    maximum = max([ques.score_for(x).complete_score.score for x in ques.emails])
    plt.figure(figsize=(15, 3))
    plt.subplot(121)
    _top_plot()
    plt.subplot(122)
    _bottom_plot()

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

def matched_difference_graph(exams, seats, gamblers_fallacy_corrections,
                             similarity_fn, similarity_name, bootstrap_count=10000,
                             path=None):
    """
    Draws a comparison graph of matched similarity differences between different exams and gambler's
        fallacy corrections.
    """
    names, matched_boots = zip(*matched_differences_bootstrap(exams, seats,
                                                              AdjacencyType.sideways_only,
                                                              gamblers_fallacy_corrections,
                                                              similarity_fn, bootstrap_count))
    xvals = list(range(len(names)))
    Bootstrap.plot_errorbars(matched_boots, fmt="*", capsize=10, color="black")
    if len(gamblers_fallacy_corrections) > 1:
        plt.xticks(xvals, [name[1] for name in names])
        plt.xlabel("Number of exams required between a pair of exams to "\
                    "allow a comparison (Gambler's Fallacy Correction)")
    plt.axhline(0, color="black")
    colors = dict(zip(exams, ("red", "blue", "green")))
    for name in exams:
        items = [i for i in range(len(names)) if names[i][0] == name]
        plt.axvspan(min(items) - 0.5, max(items) + 0.5, color=colors[name], alpha=0.3, label=name)
    plt.ylabel("One-sided 95% confidence interval of mean difference")
    plt.title("Difference in matched %s between one- and two-apart students"
              % similarity_name)
    lgd = plt.legend()
    show_or_save(path, lgd)

if __name__ == '__main__':
    grader_comparison_report()
