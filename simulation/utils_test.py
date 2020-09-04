import unittest
import networkx as nx
import utils


class TestUtils(unittest.TestCase):
    def test_probability(self):
        results = [utils.probability(0.1) for _ in range(10)]
        self.assertGreater(results.count(False), results.count(True))

        results2 = [utils.probability(1.0) for _ in range(2)]
        self.assertEqual(results2.count(True), 2)
