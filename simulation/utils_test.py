import unittest
import networkx as nx
import utils
import numpy as np


class TestUtils(unittest.TestCase):
    def test_new_probability_func(self):
        probability_func = utils.new_probability_func(seed=None)
        results = [probability_func(0.1) for _ in range(10)]
        self.assertGreater(results.count(False), results.count(True))

        results2 = [probability_func(1.0) for _ in range(2)]
        self.assertEqual(results2.count(True), 2)

    def test_new_exponential_func(self):
        exponential_func = utils.new_exponential_func(seed=None)
        result = exponential_func(loc=0, scale=100)
        self.assertGreater(result, 0)

    def test_new_gamma_func(self):
        gamma_func = utils.new_gamma_func(seed=None)
        result = gamma_func(3, loc=0.001, scale=10000)
        self.assertGreater(result, 1000)

    def test_new_random_number_func(self):
        random_number_func = utils.new_random_number_func(seed=None)
        result = random_number_func()
        self.assertTrue(result >= 0 and result <= 1)

    def test_choice_function(self):
        choice_func = utils.new_choice_func(seed=None)
        count_list = list(range(10))
        result = choice_func(count_list)
        self.assertTrue(result in count_list)
