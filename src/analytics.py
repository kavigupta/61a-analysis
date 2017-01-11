"""
A module containing a variety of functions for analyzing the data. This is supposed to be more data
    specific than statistics.
"""
import numpy as np

from tools import cached_property

def compensate_for_grader_means(evals, z_thresh=1):
    """
    Compensates for grader means by subtracting each grader's average grades per problem. Eliminates
        individuals for whom the graders are unusual.
    """
    if not evals.evaluation_for(list(evals.emails)[0]).means_need_compensation:
        return evals
    problematic = set(_identify_problematic_ranges(evals, z_thresh))
    filt = evals.remove(problematic)
    zeroed = filt.zero_meaned()
    return zeroed

class ExamPair: # pylint: disable=R0903
    """
    Structure representing a correlation between exam scores, as well as metadata on location.
    """
    def __init__(self, first, second, are_time_adjacent, are_space_adjacent, are_same_room):
        # pylint: disable=R0913
        self.are_time_adjacent = are_time_adjacent
        self.first = first
        self.second = second
        self.are_space_adjacent = are_space_adjacent
        self.are_same_room = are_same_room
    @cached_property
    def correlation(self):
        """
        The correlation between the two exam's rubric items
        """
        return self.first.correlation(self.second)
    @cached_property
    def abs_score_diff(self):
        """
        The absolute difference between the exam scores
        """
        return abs(self.first.score - self.second.score)
    def __repr__(self):
        return "ExamPair(%s, %s, %r, %r, %r)" % tuple(self)
    def __hash__(self):
        return hash((hash(self.first) + hash(self.second), tuple(self)[2:]))
    def __eq__(self, other):
        align = self.first == other.first and self.second == other.second
        mis_align = self.first == other.second and self.second == other.first
        if not align and not mis_align:
            return False
        return tuple(self)[2:] == tuple(other)[2:]
    def __iter__(self):
        return iter((self.first,
                     self.second,
                     self.are_time_adjacent,
                     self.are_space_adjacent,
                     self.are_same_room))

def all_pairs(graded_exam, seating_chart, time_delta, progress, require_same_room):
    """
    Yields an iterable of all pairs between individuals.
    """
    if require_same_room:
        for _, in_room in seating_chart.emails_by_room:
            yield from _pairs_per_individual(graded_exam, seating_chart, time_delta, progress, in_room, True)
    else:
        emails = list(graded_exam.emails)
        yield from _pairs_per_individual(graded_exam, seating_chart, time_delta, progress, emails, False)

def _pairs_per_individual(graded_exam, seating_chart, time_delta, progress, emails, known_same_room):
    p_bar = progress(len(emails))
    for index_x, email_x in enumerate(emails):
        p_bar.update(index_x)
        if email_x not in graded_exam.emails:
            continue
        eval_x = graded_exam.evaluation_for(email_x)
        if not known_same_room:
            room_x = seating_chart.room_for(email_x)
        for email_y in emails[index_x+1:]:
            if email_y not in graded_exam.emails:
                continue
            if not known_same_room:
                room_y = seating_chart.room_for(email_y)
                same_room = room_x == room_y
            else:
                same_room = True
            eval_y = graded_exam.evaluation_for(email_y)
            time_adjacent = abs(graded_exam.time_diff(email_x, email_y)) <= time_delta
            space_adjacent = seating_chart.are_adjacent(email_x, email_y)
            yield ExamPair(eval_x, eval_y, time_adjacent, space_adjacent, same_room)


def _unusualness(grader, question):
    """
    Get the unusualness of a grader with respect to a graded question; i.e., the average of the
        z scores from the overall mean for each rubric item.
    """
    overall_mean = question.mean_score
    overall_std = question.std_score
    by_grader = question.for_grader(grader)
    return np.mean((np.abs(by_grader.mean_score - overall_mean) / overall_std).rubric_items)

def _identify_problematic_ranges(evals, z_thresh):
    """
    Ouptuts an iterable of emails for which at least one grader had an unusualness greater than the
        z threshold.
    """
    for _, graded_question in evals:
        for grader in graded_question.graders:
            if _unusualness(grader, graded_question) > z_thresh:
                yield from graded_question.for_grader(grader).emails
