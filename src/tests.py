"""
Tests for various modules.
"""
from unittest import TestCase, main

from seating_chart import SeatingChart, Location
from constants import DATA_DIR
from evaluations import proc_evaluations
from analytics import compensate_for_grader_means

from numpy.testing import assert_almost_equal as aae

EVALS_SAMPLE = proc_evaluations('data/test-evals.zip')

class TestAnalytics(TestCase):
    """
    Test suite for analytics.py.
    """
    def test_compensate_for_grader_means(self):
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
