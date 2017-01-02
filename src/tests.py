
from unittest import TestCase, main

from seating_chart import SeatingChart
from constants import DATA_DIR

class TestSeatingChart(TestCase):
    chart = SeatingChart('{}/real-data/final_seats.csv'.format(DATA_DIR))
    def test_exist_emails(self):
        for email in self.chart.emails:
            self.assertEqual(type(email), str)
    def test_adjacency_consistency(self):
        for email in self.chart.emails:
            for adj_email in self.chart.sideways_items(email):
                self.assertTrue(email in self.chart.sideways_items(adj_email), str((email, adj_email)))

if __name__ == '__main__':
    main()