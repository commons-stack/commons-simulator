import unittest
from convictionvoting import trigger_threshold


class ConvictionThresholdTest(unittest.TestCase):
    def test_small_proposal_should_have_low_threshold(self):
        threshold = trigger_threshold(10, 1000, 10000000, 0.2)

        # This number is not special, just used to make sure everything stays the same
        self.assertEqual(threshold, 5540166.20498615)
