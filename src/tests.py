"""
Tests for various modules.
"""
from unittest import TestCase, main

from seating_chart import SeatingChart
from constants import DATA_DIR

class TestSeatingChart(TestCase):
    """
    Tests seating charts
    """
    chart = SeatingChart('{}/real-data/final_seats.csv'.format(DATA_DIR))
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

if __name__ == '__main__':
    main()
