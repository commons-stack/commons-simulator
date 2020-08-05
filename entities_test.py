import unittest
from unittest.mock import patch, MagicMock
from entities import Proposal, ProposalStatus, Participant
import utils


class TestProposal(unittest.TestCase):
    def test_has_enough_conviction(self):
        p = Proposal(500, 0.0)

        # a newly created Proposal can't expect to have any Conviction gathered at all
        self.assertFalse(p.has_enough_conviction(10000, 3e6))

        p.conviction = 2666666.7
        self.assertTrue(p.has_enough_conviction(10000, 3e6))


class TestParticipant(unittest.TestCase):
    def setUp(self):
        self.p = Participant()

    def test_buy(self):
        """
        Test that the function works. If we set the probability to 1, Participant should buy in.
        If we set the probability to 0, 0 will be returned.
        """
        with patch('entities.probability') as mock:
            mock.return_value = True
            # Must set Participant's sentiment artificially high, because of Zargham's force calculation
            self.p.sentiment = 1
            delta_holdings = self.p.buy()
            self.assertGreater(delta_holdings, 0)

        with patch('entities.probability') as mock:
            mock.return_value = False
            delta_holdings = self.p.buy()
            self.assertEqual(delta_holdings, 0)

    def test_sell(self):
        """
        Test that the function works. If we set the probability to 1, Participant should buy in.
        If we set the probability to 0, 0 will be returned.
        """

        with patch('entities.probability') as mock:
            mock.return_value = True
            self.p.sentiment = 0.1
            delta_holdings = self.p.sell()
            self.assertLess(delta_holdings, 0)

        with patch('entities.probability') as mock:
            mock.return_value = False
            delta_holdings = self.p.sell()
            self.assertEqual(delta_holdings, 0)

    def test_create_proposal(self):
        """
        Test that the function works. If we set the probability to 1, we should
        get True. If not, we should get False.
        """
        with patch('entities.probability') as mock:
            mock.return_value = True
            self.assertTrue(self.p.create_proposal(10000, 0.5, 100000))

        with patch('entities.probability') as mock:
            mock.return_value = False
            self.assertFalse(self.p.create_proposal(10000, 0.5, 100000))


if __name__ == '__main__':
    unittest.main()
