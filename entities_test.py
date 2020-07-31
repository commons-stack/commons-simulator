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
    def test_buy(self):
        """
        Test that the function works. If we set the probability to 1, Participant should buy in.
        If we set the probability to 0, 0 will be returned.
        """
        p = Participant()

        with patch('entities.probability') as mock:
            mock.return_value = True
            p.sentiment = 1  # Must set Participant's sentiment artificially high, because of Zargham's force calculation
            delta_holdings = p.buy()
            self.assertGreater(delta_holdings, 0)

        with patch('entities.probability') as mock:
            mock.return_value = False
            delta_holdings = p.buy()
            self.assertEqual(delta_holdings, 0)

    def test_sell(self):
        """
        Test that the function works. If we set the probability to 1, Participant should buy in.
        If we set the probability to 0, 0 will be returned.
        """
        p = Participant()

        with patch('entities.probability') as mock:
            mock.return_value = True
            p.sentiment = 0.1
            delta_holdings = p.sell()
            self.assertLess(delta_holdings, 0)

        with patch('entities.probability') as mock:
            mock.return_value = False
            delta_holdings = p.sell()
            self.assertEqual(delta_holdings, 0)


if __name__ == '__main__':
    unittest.main()
