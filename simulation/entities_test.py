import unittest
import uuid
from unittest.mock import MagicMock, patch

import numpy as np
import math

import utils
from entities import Participant, ParticipantSupport, Proposal, ProposalStatus
from hatch import TokenBatch, VestingOptions
from simulation import new_probability_func, new_random_number_func


def always(rate):
    return True


def never(rate):
    return False


class TestProposal(unittest.TestCase):
    def setUp(self):
        self.p = Proposal(500, 0.0)

    def test_update_age(self):
        self.p.update_age()

        # The Proposal's age starts at 0 and should be incremented by 1 after update_age()
        self.assertEqual(self.p.age, 1)

    def test_update_threshold(self):
        # Just check if the trigger_threshold is correct
        self.assertEqual(self.p.update_threshold(500000.0, 3000.0, 10000.0), 1500.000300000045)

        # If the proposal status is not CANDIDATE, update_threshold shoud return NaN
        self.p.status = ProposalStatus.ACTIVE
        self.assertTrue(math.isnan(self.p.update_threshold(500000.0, 3000.0, 10000.0)))

    def test_has_enough_conviction(self):
        # a newly created Proposal can't expect to have any Conviction gathered at all
        self.assertFalse(self.p.has_enough_conviction(10000, 3e6, 0.2))

        self.p.conviction = 2666666.7
        self.assertTrue(self.p.has_enough_conviction(10000, 3e6, 0.2))


class TestParticipant(unittest.TestCase):
    def setUp(self):
        self.params = {
            "probability_func": new_probability_func(seed=None),
            "random_number_func": new_random_number_func(seed=None)
        }
        self.p = Participant(TokenBatch(100, 100), self.params["probability_func"], self.params["random_number_func"])

    def test_buy(self):
        """
        Test that the function works. If we set the probability to 1, Participant should buy in.
        If we set the probability to 0, 0 will be returned.
        """

        # Must set Participant's sentiment artificially high, because of Zargham's force calculation
        self.p.sentiment = 1
        self.p._probability_func = always
        delta_holdings = self.p.buy()
        self.assertGreater(delta_holdings, 0)

        self.p._probability_func = never
        delta_holdings = self.p.buy()
        self.assertEqual(delta_holdings, 0)

    def test_sell(self):
        """
        Test that the function works. If we set the probability to 1, Participant should buy in.
        If we set the probability to 0, 0 will be returned.
        """

        self.p._probability_func = always
        self.p.sentiment = 0.1
        delta_holdings = self.p.sell()
        self.assertGreater(delta_holdings, 0)

        self.p._probability_func = never
        delta_holdings = self.p.sell()
        self.assertEqual(delta_holdings, 0)

    def test_increase_holdings(self):
        """
        Test that the function works. The result nonvesting holdings should be
        the initial nonvesting holdings plus the added nonvesting holdings.
        The vesting and the vesting_spent holdings should not me modified.
        """
        added_nonvesting_holdings = 50
        inital_nonvesting_holdings = self.p.holdings.nonvesting
        initial_vesting_holdings = self.p.holdings.vesting
        initial_vesting_spent_holdings = self.p.holdings.vesting_spent
        self.p.increase_holdings(added_nonvesting_holdings)

        self.assertEqual(self.p.holdings.nonvesting,
                        added_nonvesting_holdings + inital_nonvesting_holdings)
        # Test if vesting and vesting_spent holdings are unchanged
        self.assertEqual(self.p.holdings.vesting, initial_vesting_holdings)
        self.assertEqual(self.p.holdings.vesting_spent, initial_vesting_spent_holdings)

    def test_spend(self):
        """
        Test that the function works. It simply tests it spend() behaviours as a
        front to TokenBatch.spend() returning a tuple with vesting, vesting_spent
        and nonvesting.
        """
        self.assertEqual(self.p.spend(50), (self.p.holdings.vesting,
                                            self.p.holdings.vesting_spent,
                                            self.p.holdings.nonvesting))

    def test_create_proposal(self):
        """
        Test that the function works. If we set the probability to 1, we should
        get True. If not, we should get False.
        """

        self.p._probability_func = always
        self.assertTrue(self.p.create_proposal(10000, 0.5, 100000))

        self.p._probability_func = never
        self.assertFalse(self.p.create_proposal(10000, 0.5, 100000))

    def test_vote_on_candidate_proposals(self):
        """
        Test that the function works. If we set the probability to 1, we should
        get a dict of Proposal UUIDs that the Participant would vote on. If not,
        we should get an empty dict.
        """

        candidate_proposals = {
            0: 1.0,
            1: 1.0,
            2: 1.0,
        }
        self.p._probability_func = never
        ans = self.p.vote_on_candidate_proposals(candidate_proposals)
        self.assertFalse(ans)

        self.p._probability_func = always
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
            0: 1.0,
            1: 0.9,
            2: 0.8,
            3: 0.4,
        }
        self.p._probability_func = always
        ans = self.p.vote_on_candidate_proposals(candidate_proposals)
        reference = {
            0: 1.0,
            1: 0.9,
            2: 0.8
        }
        self.assertEqual(ans, reference)

    def test_stake_across_all_supported_proposals(self):
        """
        Test that the rebalancing code works as intended.

        Given 4 Proposals which the Participant has affinity 0.9, 0.9, 0.8, 0.6
        to, we should expect an allocation of 0.28125, 0.28125, 02.5, 0.1872
        respectively.

        The calculation should also include vesting and nonvesting TokenBatches.
        """
        supported_proposals = [
            (0.9, 0),
            (0.9, 1),
            (0.8, 2),
            (0.6, 3),
        ]

        self.p.holdings = TokenBatch(500, 500)

        ans = self.p.stake_across_all_supported_proposals(supported_proposals)
        reference = {
            0: 281.25000000000006,
            1: 281.25000000000006,
            2: 250.00000000000006,
            3: 187.5,
        }
        self.assertEqual(ans, reference)

    def test_update_token_batch_age(self):
        """
        Test that the participant token batch is updated by 1 day after
        running Participant.update_token_batch_age()
        """
        old_age_days = self.p.holdings.age_days
        new_age_days = self.p.update_token_batch_age()
        self.assertEqual(new_age_days, old_age_days + 1)

    def test_wants_to_exit(self):
        """
        Test that the function works. First force the probability to be True
        and check if the participant wanted to exit. Then force the probability
        to be False and check if the participant do not wanted to exit.
        """
        # Set a sentiment below the exit threshold
        self.p.sentiment = 0.2
        self.p._probability_func = always
        # A participant with vesting should not be able to exit
        self.assertFalse(self.p.wants_to_exit())
        self.p.holdings.vesting = 0
        # After the participant has no vesting, he can exit
        self.assertTrue(self.p.wants_to_exit())
        self.p._probability_func = never
        self.assertFalse(self.p.wants_to_exit())


class TestParticipantSupport(unittest.TestCase):
    def setUp(self):
        self.pSupport = ParticipantSupport(affinity=1)

    def test_available_fields(self):
        """
        Test that the it only has the fields currently used for defining
        participant->proposal support edges
        """
        self.assertEqual(self.pSupport._fields, ('affinity', 'tokens', 'conviction', 'is_author'))

    def test_default_values(self):
        """
        Test it assigns default values to all other fields
        """
        self.assertEqual(self.pSupport.affinity, 1)
        self.assertEqual(self.pSupport.tokens, 0)
        self.assertEqual(self.pSupport.conviction, 0)
        self.assertEqual(self.pSupport.is_author, False)
