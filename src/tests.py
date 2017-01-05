"""
Tests for various modules.
"""
from unittest import TestCase, main

from math import sqrt

from numpy.testing import assert_almost_equal as aae

from seating_chart import SeatingChart, Location
from constants import DATA_DIR
from evaluations import proc_evaluations
from analytics import compensate_for_grader_means, all_correlations, Correlation, _unusualness
from graded_exam import ExamQuestion


EVALS_SAMPLE = proc_evaluations('data/test-evals.zip')
EVALS_SIMPLE_SAMPLE = proc_evaluations('data/test-simple-evals.zip')
SEATS_SAMPLE = SeatingChart('data/test-seats.csv')
SEATS_SIMPLE_SAMPLE = SeatingChart('data/test-seats-simple.csv')

class TestAnalytics(TestCase):
    """
    Test suite for analytics.py.
    """
    @staticmethod
    def test_compensate_for_grader_means(): # pylint: disable=C0103
        """
        Tests the compensate_for_grader_means function (only the compensation, not the filtering)
            by running it on a sample and testing two individuals to check that they were adjusted
            appropriately.
        """
        compensated = compensate_for_grader_means(EVALS_SAMPLE, 1000)
        q_eval = compensated.evaluation_for('Q@berkeley.edu').evals
        aae(+0.625, q_eval[0].complete_score.score)
        aae(+1.000, q_eval[1].complete_score.score)
        aae(-0.500, q_eval[2].complete_score.score)
        p_eval = compensated.evaluation_for("P@berkeley.edu").evals
        aae(+2-3.5/3, p_eval[0].complete_score.score)
        aae(+0.300, p_eval[1].complete_score.score)
        aae(-0.500, p_eval[2].complete_score.score)
    def test_all_correlations(self):
        """
        Tests the all_correlations method by exact checking on a small test case.
        """
        corrs = list(all_correlations(EVALS_SIMPLE_SAMPLE, SEATS_SIMPLE_SAMPLE, 1))
        self.assertEqual(6, len(corrs))
        expect_cors = {
            "QW" : Correlation(0, True, True, True),
            "QE" : Correlation(1/sqrt(2), False, False, False),
            "QR" : Correlation(1/sqrt(2), False, False, False),
            "WE" : Correlation(0, True, False, False),
            "WR" : Correlation(0, False, False, False),
            "ER" : Correlation(1, True, False, True)
        }.values()
        self.assertEqual(set(expect_cors), set(corrs))
    @staticmethod
    def test_unusualness():
        """
        Checks unusualness on small sample.

        For calculations, see calculation-of-unusualness.odt, which uses the bernouili random
            variable variance p(1-p).
        """
        question = ExamQuestion(EVALS_SAMPLE, 1)
        actual = _unusualness("Grader A", question)
        expected = 0.1800983877
        aae(expected, actual)

class TestExamQuestion(TestCase):
    """
    Tests the exam question class
    """
    def test_for_grader(self):
        """
        Tests to make sure for_grader works to specification.
        """
        question = ExamQuestion(EVALS_SAMPLE, 1)
        self.assertEqual({"Grader %s" % g for g in "ABC"}, question.graders)
        for grader in question.graders:
            self.assertEqual({grader}, question.for_grader(grader).graders)
        all_emails = sorted(x for g in question.graders for x in question.for_grader(g).emails)
        self.assertEqual(sorted(question.emails), all_emails)

class TestGradedExams(TestCase):
    """
    Tests the graded exams class
    """
    def test_by_rooms(self):
        """
        Tests the function by_rooms, which splits the exam into several for each room.
        """
        by_rooms = list(EVALS_SAMPLE.by_room(SEATS_SAMPLE))
        all_emails = sorted(x for _, y in by_rooms for x in y.emails)
        self.assertEqual(all_emails, sorted(EVALS_SAMPLE.emails))
        for room, exam in by_rooms:
            for email in exam.emails:
                self.assertEqual(room, SEATS_SAMPLE.room_for(email))
                self.assertEqual(exam.evaluation_for(email), EVALS_SAMPLE.evaluation_for(email))
    def test_remove(self):
        """
        Tests the function remove, which removes some email addresses.
        """
        some_emails = list(EVALS_SAMPLE.emails)[::3]
        removed = EVALS_SAMPLE.remove(some_emails)
        self.assertEqual(sorted(list(removed.emails) + some_emails), sorted(EVALS_SAMPLE.emails))
    def test_time_diff(self):
        """
        Tests the time_diff function thoroughly on a evals_sample.
        """
        emails = [x + "@berkeley.edu" for x in "QWERTYUIOP"]
        for index_a, email_a in enumerate(emails):
            for index_b, email_b in enumerate(emails):
                self.assertEqual(index_a - index_b, EVALS_SAMPLE.time_diff(email_a, email_b))

class TestSeatingChart(TestCase):
    """
    Tests seating charts
    """
    chart = SeatingChart('{}/real-data/mt1_seats.csv'.format(DATA_DIR))
    def test_exist_emails(self):
        """
        Test that the emails all exist and are strings.
        """
        for email in self.chart.emails:
            self.assertEqual(type(email), str)
    def test_adjacency_consistency(self):
        """
        Test to make sure that X is right of Y <--> Y is left of X
        """
        for email in self.chart.emails:
            for adj_email in self.chart.sideways_items(email):
                adj_adj_email = self.chart.sideways_items(adj_email)
                self.assertTrue(email in adj_adj_email, str((email, adj_email)))
    def test_adjacency(self):
        """
        Test of adjacency, from sample seating chart.
        """
        seats = SeatingChart('data/test-seats-complex.csv')
        self.assertEqual({"R@berkeley.edu", "T@berkeley.edu"}, set(seats.adjacent_to("Q@berkeley.edu")))
        self.assertEqual({"O@berkeley.edu", "T@berkeley.edu", "U@berkeley.edu"}, set(seats.adjacent_to("Y@berkeley.edu")))
        self.assertEqual(set(), set(seats.adjacent_to("A@berkeley.edu")), "Nothing adjacent to something in a different room")

class TestLocation(TestCase):
    """
    Tests facets of the location parsing system
    """
    def test_basic_format(self):
        """
        Tests that the (LETTER:ROW)(NUMBER:COLUMN) format is preserved.
        """
        self.assertEqual(Location('room', row=3, column=2),
                         Location.create_location("room", "D2"))
        self.assertEqual(Location('room', row=0, column=12),
                         Location.create_location("room", "A12"))

if __name__ == '__main__':
    main()
