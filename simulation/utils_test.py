import unittest
import networkx as nx
import utils
import numpy as np


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.params = {"random_state": np.random.RandomState(None)}

    def test_probability(self):
        results = [utils.probability(0.1, self.params["random_state"]) for _ in range(10)]
        self.assertGreater(results.count(False), results.count(True))

        results2 = [utils.probability(1.0, self.params["random_state"]) for _ in range(2)]
        self.assertEqual(results2.count(True), 2)

if __name__ == "__main__":
    unittest.main()