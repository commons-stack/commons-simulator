import unittest
import uuid
from unittest.mock import MagicMock, patch

import utils
from entities import Participant, Proposal, ProposalStatus
from hatch import TokenBatch


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

    def test_vote_on_candidate_proposals(self):
        """
        Test that the function works. If we set the probability to 1, we should
        get a dict of Proposal UUIDs that the Participant would vote on. If not,
        we should get an empty dict.
        """

        candidate_proposals = {
            uuid.UUID(int=179821351946450230734044638685583215499): 1.0,
            uuid.UUID(int=215071290061070589371009813111193284959): 1.0,
            uuid.UUID(int=20468923874830131214536379780280861909): 1.0,
        }
        with patch('entities.probability') as mock:
            mock.return_value = False
            ans = self.p.vote_on_candidate_proposals(candidate_proposals)
            self.assertFalse(ans)

        with patch('entities.probability') as mock:
            mock.return_value = True
            ans = self.p.vote_on_candidate_proposals(candidate_proposals)
            self.assertEqual(len(ans), 3)

    def test_vote_on_candidate_proposals_zargham_algorithm(self):
        """
        Test that Zargham's algorithm works as intended.

        A cutoff value is set based on your affinity to your favourite Proposal.
        If there are other Proposals that you like almost as much, you will vote
        for them too, otherwise if they don't meet the cutoff value you will
        only vote for your favourite Proposal.
        """

        candidate_proposals = {
            uuid.UUID(int=179821351946450230734044638685583215499): 1.0,
            uuid.UUID(int=215071290061070589371009813111193284959): 0.9,
            uuid.UUID(int=20468923874830131214536379780280861909): 0.8,
            uuid.UUID(int=268821512376988039567204465930241984322): 0.4,
        }
        with patch('entities.probability') as mock:
            mock.return_value = True
            ans = self.p.vote_on_candidate_proposals(candidate_proposals)
            self.assertIn(
                uuid.UUID(int=179821351946450230734044638685583215499), ans)
            self.assertIn(
                uuid.UUID(int=215071290061070589371009813111193284959), ans)
            self.assertIn(
                uuid.UUID(int=20468923874830131214536379780280861909), ans)
            self.assertNotIn(
                uuid.UUID(int=268821512376988039567204465930241984322), ans)

    def test_stake_across_all_supported_proposals(self):
        """
        Test that the rebalancing code works as intended.

        Given 4 Proposals which the Participant has affinity 0.9, 0.9, 0.8, 0.6
        to, we should expect an allocation of 0.28125, 0.28125, 02.5, 0.1872
        respectively.

        The calculation should also include vesting and nonvesting TokenBatches.
        """
        p = [Proposal(0, 0) for _ in range(4)]
        p[0].uuid = uuid.UUID(int=179821351946450230734044638685583215499)
        p[1].uuid = uuid.UUID(int=215071290061070589371009813111193284959)
        p[2].uuid = uuid.UUID(int=20468923874830131214536379780280861909)
        p[3].uuid = uuid.UUID(int=268821512376988039567204465930241984322)
        supported_proposals = [
            (0.9, p[0]),
            (0.9, p[1]),
            (0.8, p[2]),
            (0.6, p[3]),
        ]

        self.p.holdings_vesting = TokenBatch(500)
        self.p.holdings_nonvesting = TokenBatch(500)

        ans = self.p.stake_across_all_supported_proposals(supported_proposals)
        print(ans)

        self.assertEqual(
            ans[uuid.UUID(int=179821351946450230734044638685583215499)], 281.25000000000006)
        self.assertEqual(
            ans[uuid.UUID(int=215071290061070589371009813111193284959)], 281.25000000000006)
        self.assertEqual(
            ans[uuid.UUID(int=20468923874830131214536379780280861909)], 250.00000000000006)
        self.assertEqual(
            ans[uuid.UUID(int=268821512376988039567204465930241984322)], 187.5)


if __name__ == '__main__':
    unittest.main()
