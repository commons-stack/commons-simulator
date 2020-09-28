import copy
import unittest
from collections import namedtuple
from unittest.mock import patch

from entities import Proposal, ProposalStatus
from hatch import Commons, TokenBatch, VestingOptions
from network_utils import bootstrap_network, add_proposal, get_edges_by_type, get_participants
from policies import (GenerateNewFunding, GenerateNewParticipant,
                      GenerateNewProposal, ActiveProposals, ProposalFunding, ParticipantVoting)


class TestGenerateNewParticipant(unittest.TestCase):
    def setUp(self):
        self.commons = Commons(10000, 1000)
        self.sentiment = 0.5
        self.network = bootstrap_network([TokenBatch(1000, VestingOptions(10, 30))
                                          for _ in range(4)], 1, 3000, 4e6, 0.2)

    def test_p_randomly(self):
        """
        Simply test that the code runs.
        """
        state = {
            "commons": self.commons,
            "sentiment": self.sentiment
        }
        with patch("policies.probability") as p:
            p.return_value = True
            ans = GenerateNewParticipant.p_randomly(None, 0, 0, state)
            self.assertEqual(ans["new_participant"], True)
            self.assertIsNotNone(ans["new_participant_investment"])
            self.assertIsNotNone(ans["new_participant_tokens"])

    def test_su_add_to_network(self):
        """
        Test that the state update function did add the Participant to the
        network, and that the network maintained its integrity (i.e. all edges
        were properly setup)
        """
        with patch("network_utils.influence") as p:
            p.return_value = 0.8

            n_old_len = len(self.network.nodes)

            _input = {
                "new_participant": True,
                "new_participant_investment": 16.872149388283283,
                "new_participant_tokens": 1.0545093367677052
            }
            _, network = GenerateNewParticipant.su_add_to_network(
                None, 0, 0, {"network": self.network.copy()}, _input)
            network_len = len(network.nodes)

            self.assertEqual(n_old_len, 5)
            self.assertEqual(network_len, 6)
            self.assertEqual(network.nodes(data="item")[
                             5].holdings_nonvesting.value, 1.0545093367677052)

            # There are 4 Participants in the network, all of them should have
            # influence edges to the newly added Participant.
            self.assertEqual(len(network.in_edges(5)), 4)
            # Check that all of these edges are support type edges.
            for u, v in network.in_edges(5):
                self.assertEqual(network.edges[u, v]["type"], "influence")


class TestGenerateNewProposal(unittest.TestCase):
    def setUp(self):
        self.network = bootstrap_network([TokenBatch(1000, VestingOptions(10, 30))
                                          for _ in range(4)], 1, 3000, 4e6, 0.2)

    def test_p_randomly(self):
        """
        Simply test that the code runs.
        """
        with patch("entities.probability") as p:
            p.return_value = True
            ans = GenerateNewProposal.p_randomly(
                None, 0, 0, {"network": self.network, "funding_pool": 100000})
            self.assertTrue(ans["new_proposal"])
            self.assertIn("proposed_by_participant", ans)

            p.return_value = False
            ans = GenerateNewProposal.p_randomly(
                None, 0, 0, {"network": self.network, "funding_pool": 100000})
            self.assertFalse(ans["new_proposal"])

    def test_su_add_to_network(self):
        """
        Test that the state update function did add a new Proposal to the
        network, and that the network maintained its integrity (i.e. all edges
        were properly setup)
        """
        result_from_policy = {
            "proposed_by_participant": 0,
            "new_proposal": True,
        }
        state = {"network":  self.network.copy(),
                 "funding_pool": 100000, "token_supply": 10000}
        _, network = GenerateNewProposal.su_add_to_network(
            [{"max_proposal_request": 0.2}], 0, 0, state, result_from_policy)
        self.assertEqual(len(network.nodes), 6)
        self.assertIsInstance(network.nodes[5]["item"], Proposal)

        # There are 4 Participants in the network, all of them should have edges
        # to the newly added Proposal.
        self.assertEqual(len(network.in_edges(5)), 4)
        # Check that all of these edges are support type edges.
        for u, v in network.in_edges(5):
            self.assertEqual(network.edges[u, v]["type"], "support")

        # Check that the Participant that created the Proposal has an affinity
        # of 1 towards it
        self.assertEqual(network.edges[0, 5]["affinity"], 1)


class TestGenerateNewFunding(unittest.TestCase):
    def test_p_exit_tribute_of_average_speculator_position_size(self):
        """
        Simply test that the code works.
        """
        m_commons = namedtuple("MockCommons", "exit_tribute")
        m_commons.exit_tribute = 0.10
        state = {
            "commons": m_commons}
        ans = GenerateNewFunding.p_exit_tribute_of_average_speculator_position_size(
            None, 0, 0, state)
        self.assertTrue(ans["funding"] > 0)

    def test_su_add_funding(self):
        commons = Commons(10000, 100)
        _, commons_new = GenerateNewFunding.su_add_funding(
            None, 0, 0, {"commons": copy.copy(commons)}, {"funding": 111})

        self.assertEqual(commons_new._funding_pool, 2111)


class TestActiveProposals(unittest.TestCase):
    def setUp(self):
        self.network = bootstrap_network([TokenBatch(1000, VestingOptions(10, 30))
                                          for _ in range(4)], 1, 3000, 4e6, 0.2)

        self.network, _ = add_proposal(self.network, Proposal(100, 1))

        self.network.nodes[4]["item"].status = ProposalStatus.ACTIVE
        self.network.nodes[5]["item"].status = ProposalStatus.ACTIVE

    def test_p_influenced_by_grant_size(self):
        """
        Simply test that the code works.
        """
        with patch("policies.probability") as p:
            p.return_value = True
            ans = ActiveProposals.p_influenced_by_grant_size(
                None, 0, 0, {"network": copy.copy(self.network)})

            self.assertEqual(ans["failed"], [4, 5])

    def test_su_set_proposal_status(self):
        """
        Simply test that the code works.
        """
        _, network1 = ActiveProposals.su_set_proposal_status(
            None, 0, 0, {"network": copy.copy(self.network)}, {"failed": [4, 5]})
        self.assertEqual(network1.nodes[4]
                         ["item"].status, ProposalStatus.FAILED)
        self.assertEqual(network1.nodes[5]
                         ["item"].status, ProposalStatus.FAILED)


class TestProposalFunding(unittest.TestCase):
    def setUp(self):
        self.network = bootstrap_network([TokenBatch(1000, VestingOptions(10, 30))
                                          for _ in range(4)], 1, 3000, 4e6, 0.2)

        self.network, _ = add_proposal(self.network, Proposal(100, 1))

        self.network.nodes[4]["item"].status = ProposalStatus.CANDIDATE
        self.network.nodes[5]["item"].status = ProposalStatus.CANDIDATE

    def test_p_compare_conviction_and_threshold(self):
        """
        Simply test that the code runs.
        """
        ProposalFunding.p_compare_conviction_and_threshold(
            [{"max_proposal_request": 0.2}], 0, 0, {"network": copy.copy(self.network), "funding_pool": 1000, "token_supply": 1000})

    def test_su_update_gathered_conviction(self):
        """
        Ensure that the edge attributes "conviction" and "tokens" were updated.
        """
        _, n_network = ProposalFunding.su_update_gathered_conviction(
            [{"days_to_80p_of_max_voting_weight": 10}], 0, 0, {"network": copy.copy(self.network), "funding_pool": 1000, "token_supply": 1000}, {})
        support_edges = get_edges_by_type(n_network, "support")

        # Make sure the conviction actually changed
        for i, j in support_edges:
            edge = n_network.edges[i, j]
            self.assertNotEqual(edge["tokens"], 0)
            self.assertNotEqual(edge["conviction"], 0)


class TestParticipantVoting(unittest.TestCase):
    def setUp(self):
        self.network = bootstrap_network([TokenBatch(1000, VestingOptions(10, 30))
                                          for _ in range(4)], 1, 3000, 4e6, 0.2)

        self.network, _ = add_proposal(self.network, Proposal(100, 1))

        """
        For proper testing, we need to make sure the Proposals are CANDIDATE and
        ensure Proposal-Participant affinities are not some random value
        """
        self.network.nodes[4]["item"].status = ProposalStatus.CANDIDATE
        self.network.nodes[5]["item"].status = ProposalStatus.CANDIDATE
        support_edges = get_edges_by_type(self.network, "support")
        for u, v in support_edges:
            self.network[u][v]["affinity"] = 0.9

    def test_p_participant_votes_on_proposal_according_to_affinity(self):
        """
        Ensure that when a Participant votes on 2 Proposals of equal affinity,
        he will split his tokens 50-50 between them.
        """
        with patch("entities.probability") as p:
            p.return_value = True
            ans = ParticipantVoting.p_participant_votes_on_proposal_according_to_affinity(
                [{"debug": False}], 0, 0, {"network": copy.copy(self.network), "funding_pool": 1000, "token_supply": 1000})

            reference = {
                'participants_stake_on_proposals': {0: {4: 500.0, 5: 500.0},
                                                    1: {4: 500.0, 5: 500.0},
                                                    2: {4: 500.0, 5: 500.0},
                                                    3: {4: 500.0, 5: 500.0}
                                                    }
            }
            self.assertEqual(ans, reference)

    def test_p_participant_votes_on_proposal_according_to_affinity_vesting_nonvesting(self):
        """
        Ensure that when a Participant with vesting and nonvesting tokens votes
        on 2 Proposals of equal affinity, all of his tokens will be split 50-50
        between them.
        """
        participants = get_participants(self.network)
        for _, participant in participants:
            participant.holdings_nonvesting = TokenBatch(1000)

        with patch("entities.probability") as p:
            p.return_value = True
            ans = ParticipantVoting.p_participant_votes_on_proposal_according_to_affinity(
                [{"debug": False}], 0, 0, {"network": copy.copy(self.network), "funding_pool": 1000, "token_supply": 1000})

            reference = {
                'participants_stake_on_proposals': {0: {4: 1000.0, 5: 1000.0},
                                                    1: {4: 1000.0, 5: 1000.0},
                                                    2: {4: 1000.0, 5: 1000.0},
                                                    3: {4: 1000.0, 5: 1000.0}
                                                    }
            }
            self.assertEqual(ans, reference)

    def test_su_update_participants_votes_and_recalculate_conviction(self):
        """
        Ensure that a Proposal with 4 Participants, each staking 1000 tokens on
        it, and no prior conviction, will have a total conviction of 4000.
        """
        _input = {
            'participants_stake_on_proposals': {0: {4: 1000.0, 5: 1200.0},
                                                1: {4: 1000.0, 5: 1200.0},
                                                2: {4: 1000.0, 5: 1200.0},
                                                3: {4: 1000.0, 5: 1200.0}
                                                }
        }
        ans = ParticipantVoting.su_update_participants_votes_and_recalculate_conviction([{"debug": False, "days_to_80p_of_max_voting_weight": 10}], 0, 0, {
            "network": copy.copy(self.network), "funding_pool": 1000, "token_supply": 1000}, _input)

        n_new = ans[1]

        self.assertEqual(calc_total_conviction(n_new, 4), 1000*4)
        self.assertEqual(calc_total_conviction(n_new, 5), 1200*4)

    def test_su_update_participants_votes_and_recalculate_conviction_prior_conviction(self):
        """
        Ensure that a support edge to a Proposal, with a stake of 1000 tokens
        and 100 prior conviction, will have a conviction of 1000+(100 *
        days_to_80p_of_max_voting_weight).
        """
        _input = {
            'participants_stake_on_proposals': {0: {4: 1000.0, 5: 1200.0},
                                                1: {4: 1000.0, 5: 1200.0},
                                                2: {4: 1000.0, 5: 1200.0},
                                                3: {4: 1000.0, 5: 1200.0}
                                                }
        }
        support_edges = get_edges_by_type(self.network, "support")
        for u, v in support_edges:
            self.network[u][v]["conviction"] = 100

        _, n_new = ParticipantVoting.su_update_participants_votes_and_recalculate_conviction([{"debug": False, "days_to_80p_of_max_voting_weight": 10}], 0, 0, {
            "network": copy.copy(self.network), "funding_pool": 1000, "token_supply": 1000}, _input)

        for u, v in support_edges:
            if v == 4:
                self.assertEqual(n_new[u][v]["conviction"], 2000)
            if v == 5:
                self.assertEqual(n_new[u][v]["conviction"], 2200)
