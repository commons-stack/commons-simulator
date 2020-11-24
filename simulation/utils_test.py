import unittest
import networkx as nx
import utils
import numpy as np


class TestUtils(unittest.TestCase):
    def test_new_probability_func(self):
        probability = utils.new_probability_func(seed=None) 
        results = [probability(0.1) for _ in range(10)]
        self.assertGreater(results.count(False), results.count(True))

        results2 = [probability(1.0) for _ in range(2)]
        self.assertEqual(results2.count(True), 2)

    def test_new_exponential_func(self):
        exponential = utils.new_exponential_func(seed=None)
        result = exponential(loc=0, scale=100)
        self.assertGreater(result, 0)

    def test_new_gamma_func(self):
        gamma = utils.new_gamma_func(seed=None)
        result = gamma(3, loc=0.001, scale=10000)
        self.assertGreater(result, 1000)
    
    def test_new_random_number_func(self):
        random_number = utils.new_random_number_func(seed=None)
        result = random_number()
        self.assertTrue(result >= 0 and result <= 1)

    def test_choice_function(self):
        choice = utils.new_choice_func(seed=None)
        count_list = list(range(10))
        result = choice(count_list)
        self.assertTrue(result in count_list)