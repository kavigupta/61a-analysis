"""
A module containing a variety of functions for analyzing the data. This is supposed to be more data
    specific than statistics.
"""
import numpy as np

def unusualness(grader, question):
    """
    Get the unusualness of a grader with respect to a graded question; i.e., the average of the
        z scores from the overall mean for each rubric item.
    """
    overall_mean = question.mean_rubric
    overall_std = question.std_rubric
    by_grader = question.for_grader(grader)
    return np.mean(np.abs(by_grader.mean_rubric - overall_mean) / overall_std)

def identify_problematic_ranges(evals, z_thresh):
    """
    Ouptuts an iterable of emails for which at least one grader had an unusualness greater than the
        z threshold.
    """
    for _, graded_question in evals:
        for grader in graded_question.graders:
            if unusualness(grader, graded_question) > z_thresh:
                yield from graded_question.for_grader(grader).emails

def compensate_for_grader_means(evals, z_thresh=1):
    """
    Compensates for grader means by subtracting each grader's average grades per problem. Eliminates
        individuals for whom the graders are unusual.
    """
    problematic = set(identify_problematic_ranges(evals, z_thresh))
    filt = evals.remove(problematic)
    zeroed = filt.zero_meaned()
    return zeroed

class Correlation: # pylint: disable=R0903
    """
    Structure representing a correlation between exam scores, as well as metadata on location.
    """
    def __init__(self, correlation, are_time_adjacent, are_space_adjacent, are_same_room):
        self.are_time_adjacent = are_time_adjacent
        self.correlation = correlation
        self.are_space_adjacent = are_space_adjacent
        self.are_same_room = are_same_room

def all_correlations(graded_exam, seating_chart, time_delta):
    """
    Yields an iterable of all Correlations between individuals.
    """
    emails = list(graded_exam.emails)
    for index_x, email_x in enumerate(emails):
        if index_x % 100 == 0:
            print(index_x, len(emails))
        if email_x not in graded_exam.emails:
            continue
        eval_x = graded_exam.evaluation_for(email_x)
        for email_y in emails[index_x+1:]:
            if email_y not in graded_exam.emails:
                continue
            eval_y = graded_exam.evaluation_for(email_y)
            time_adjacent = abs(graded_exam.time_diff(email_x, email_y)) <= time_delta
            correl = eval_x.correlation(eval_y)
            space_adjacent = seating_chart.are_adjacent(email_x, email_y)
            same_room = seating_chart.same_room(email_x, email_y)
            yield Correlation(correl, time_adjacent, space_adjacent, same_room)
