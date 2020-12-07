import copy
import unittest
from collections import namedtuple
from os.path import commonpath
from unittest.mock import patch
import numpy as np

import networkx as nx

from utils import (new_probability_func, new_exponential_func,
                   new_gamma_func, new_random_number_func,
                   new_choice_func)
from entities import Proposal, ProposalStatus
from hatch import Commons, TokenBatch, VestingOptions
from network_utils import (add_proposal, bootstrap_network,
                           calc_total_conviction, get_edges_by_type,
                           get_participants, get_proposals,
                           setup_conflict_edges)
from policies import (ActiveProposals, GenerateNewFunding,
                      GenerateNewParticipant, GenerateNewProposal,
                      ParticipantBuysTokens, ParticipantExits,
                      ParticipantSellsTokens, ParticipantVoting,
                      ProposalFunding)


def always(rate):
    return True


def never(rate):
    return False


class TestGenerateNewParticipant(unittest.TestCase):
    def setUp(self):
        self.commons = Commons(10000, 1000)
        self.sentiment = 0.5
        self.params = {
            "debug": False,
            "probability_func": new_probability_func(seed=None),
            "exponential_func": new_exponential_func(seed=None),
            "gamma_func": new_gamma_func(seed=None),
            "random_number_func": new_random_number_func(seed=None)
        }
        self.network = bootstrap_network([TokenBatch(1000, 0, vesting_options=VestingOptions(10, 30))
                                          for _ in range(4)], 1, 3000, 4e6, 0.2, self.params["probability_func"],
                                          self.params["random_number_func"], self.params["gamma_func"],
                                          self.params["exponential_func"])

    def test_p_randomly(self):
        """
        Simply test that the code runs.
        """
        state = {
            "commons": self.commons,
            "sentiment": self.sentiment
        }
        self.params["probability_func"] = always
        ans = GenerateNewParticipant.p_randomly(self.params, 0, 0, state)
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
                self.params, 0, 0, {"network": self.network.copy()}, _input)
            network_len = len(network.nodes)

            self.assertEqual(n_old_len, 5)
            self.assertEqual(network_len, 6)
            self.assertEqual(network.nodes(data="item")[
                             5].holdings.total, 1.0545093367677052)

            # There are 4 Participants in the network, all of them should have
            # influence edges to the newly added Participant.
            self.assertEqual(len(network.in_edges(5)), 4)
            # Check that all of these edges are support type edges.
            for u, v in network.in_edges(5):
                self.assertEqual(network.edges[u, v]["type"], "influence")

<<<<<<< HEAD
    def test_su_update_participants_token_batch_age(self):
        """
        Test that after running the state update function the participants'
        token batch age in days are incremented by one
        """
        _input = {}
        _, network = GenerateNewParticipant.su_update_participants_token_batch_age(
                self.params, 0, 0, {"network": self.network.copy()}, _input)
        participants = get_participants(network)
        for i, participant in participants:
            self.assertEqual(participant.holdings.age_days, 1)

=======
>>>>>>> c449d87da4dc718d10e22befbd748d8081321535
    def test_su_add_investment_to_commons(self):
        old_token_supply = self.commons._token_supply
        old_collateral_pool = self.commons._collateral_pool
        commons = GenerateNewParticipant.su_add_investment_to_commons(
            self.params, 0, 0, {"commons": self.commons},
                               {"new_participant": False})

        # Check if case there is no new participant, the token supply and
        # the collateral pool do not change.
        self.assertEqual(self.commons._token_supply, old_token_supply)
        self.assertEqual(self.commons._collateral_pool, old_collateral_pool)
        _input = {
                "new_participant": True,
                "new_participant_investment": 16.872149388283283,
                "new_participant_tokens": 1.0545093367677052
            }
        GenerateNewParticipant.su_add_investment_to_commons(
            self.params, 0, 0, {"commons": self.commons}, _input)

        self.assertEqual(self.commons._token_supply, 1001.0539539273273)
        self.assertEqual(self.commons._collateral_pool, 8016.872149388283)


class TestGenerateNewProposal(unittest.TestCase):
    def setUp(self):
        self.params = {
            "max_proposal_request": 0.2,
            "probability_func": new_probability_func(seed=None),
            "exponential_func": new_exponential_func(seed=None),
            "gamma_func": new_gamma_func(seed=None),
            "random_number_func": new_random_number_func(seed=None),
            "choice_func": new_choice_func(seed=None)
        }
        self.network = bootstrap_network([TokenBatch(1000, 0, vesting_options=VestingOptions(10, 30))
                                          for _ in range(4)], 1, 3000, 4e6, 0.2, self.params["probability_func"],
                                          self.params["random_number_func"], self.params["gamma_func"],
                                          self.params["exponential_func"])

    def test_p_randomly(self):
        """
        Simply test that the code runs.
        """
        with patch("entities.Participant.create_proposal") as p:
            p.return_value = True
            ans = GenerateNewProposal.p_randomly(
                self.params, 0, 0, {"network": self.network, "funding_pool": 100000})
            self.assertTrue(ans["new_proposal"])
            self.assertIn("proposed_by_participant", ans)

            p.return_value = False
            ans = GenerateNewProposal.p_randomly(
            self.params, 0, 0, {"network": self.network, "funding_pool": 100000})
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
            self.params, 0, 0, state, result_from_policy)
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
    def setUp(self):
        self.params = {"exponential_func": new_exponential_func(seed=None)}

    def test_p_exit_tribute_of_average_speculator_position_size(self):
        """
        Simply test that the code works.
        """
        m_commons = namedtuple("MockCommons", "exit_tribute")
        m_commons.exit_tribute = 0.10
        state = {
            "commons": m_commons}
        ans = GenerateNewFunding.p_exit_tribute_of_average_speculator_position_size(
            self.params, 0, 0, state)
        self.assertTrue(ans["funding"] > 0)

    def test_su_add_funding(self):
        commons = Commons(10000, 100)
        _, commons_new = GenerateNewFunding.su_add_funding(
            None, 0, 0, {"commons": copy.copy(commons)}, {"funding": 111})

        self.assertEqual(commons_new._funding_pool, 2111)


class TestActiveProposals(unittest.TestCase):
    def setUp(self):
        self.params = {
            "probability_func": new_probability_func(seed=None),
            "exponential_func": new_exponential_func(seed=None),
            "gamma_func": new_gamma_func(seed=None),
            "random_number_func": new_random_number_func(seed=None)
        }
        self.network = bootstrap_network([TokenBatch(1000, 0, vesting_options=VestingOptions(10, 30))
                                          for _ in range(4)], 1, 3000, 4e6, 0.2, self.params["probability_func"],
                                          self.params["random_number_func"], self.params["gamma_func"],
                                          self.params["exponential_func"])

        self.network, _ = add_proposal(self.network, Proposal(100, 1), self.params["random_number_func"])

        self.network.nodes[4]["item"].status = ProposalStatus.ACTIVE
        self.network.nodes[5]["item"].status = ProposalStatus.ACTIVE

    def test_p_influenced_by_grant_size(self):
        """
        Simply test that the code works.
        """
        self.params["probability_func"] = always
        ans = ActiveProposals.p_influenced_by_grant_size(
            self.params, 0, 0, {"network": copy.copy(self.network)})

        self.assertEqual(ans["failed"], [4, 5])

    def test_su_set_proposal_status(self):
        """
        Simply test that the code works.
        """
        _, network1 = ActiveProposals.su_set_proposal_status(
            None, 0, 0, {"network": copy.copy(self.network)}, {"failed": [4], "succeeded": [5]})
        self.assertEqual(network1.nodes[4]
                         ["item"].status, ProposalStatus.FAILED)
        self.assertEqual(network1.nodes[5]
                         ["item"].status, ProposalStatus.COMPLETED)


class TestProposalFunding(unittest.TestCase):
    def setUp(self):
        self.params = {
            "max_proposal_request": 0.2,
            "alpha_days_to_80p_of_max_voting_weight": 10,
            "probability_func": new_probability_func(seed=None),
            "exponential_func": new_exponential_func(seed=None),
            "gamma_func": new_gamma_func(seed=None),
            "random_number_func": new_random_number_func(seed=None)
        }
        self.commons = Commons(1000, 1000)
        self.network = bootstrap_network([TokenBatch(1000, 0, vesting_options=VestingOptions(10, 30))
                                          for _ in range(4)], 1, 3000, 4e6, 0.2, self.params["probability_func"],
                                          self.params["random_number_func"], self.params["gamma_func"],
                                          self.params["exponential_func"])

        self.network, _ = add_proposal(self.network, Proposal(100, 1), self.params["random_number_func"])

        self.network.nodes[4]["item"].status = ProposalStatus.CANDIDATE
        self.network.nodes[5]["item"].status = ProposalStatus.CANDIDATE

    def test_p_compare_conviction_and_threshold(self):
        """
        Simply test that the code runs.
        """
        ProposalFunding.p_compare_conviction_and_threshold(
            self.params, 0, 0, {"network": copy.copy(self.network), "funding_pool": 1000, "token_supply": 1000})

    def test_su_make_proposal_active(self):
        """
        Simply test that the code runs.
        """
        _input = {
            "proposal_idxs_with_enough_conviction": [4, 5]
        }
        _, n_new = ProposalFunding.su_make_proposal_active(
            self.params, 0, 0, {"network": copy.copy(self.network), "funding_pool": 1000, "token_supply": 1000}, _input)
        for i in [4, 5]:
            self.assertEqual(
                n_new.nodes[i]["item"].status, ProposalStatus.ACTIVE)

    def test_su_deduct_funds_from_funding_pool(self):
        """
        Test that the code runs and if there is any proposal with enough
        conviction, the fund requested by the proposal will be deducted
        from de funding pool.
        """
        _input = {"proposal_idxs_with_enough_conviction": [3]}
        network_copy = copy.copy(self.network)
        network_copy.nodes[3]["item"].funds_requested = 50
        old_funding_pool = self.commons._funding_pool
        ProposalFunding.su_deduct_funds_from_funding_pool(
            self.params, 0, 0, {"commons": self.commons,"network": network_copy, "funding_pool": 1000, "token_supply": 1000}, _input)
        self.assertEqual(self.commons._funding_pool, old_funding_pool-50)

    def test_su_update_age_and_conviction_thresholds(self):
        """
        Test that Proposal's age and conviction threshold are being updated.
        The initial Proposal's age is 0, so it expects that both proposals increased
        by 1 after the state update function.
        """
        _input = {}
        ProposalFunding.su_update_age_and_conviction_thresholds(
            self.params, 0, 0, {"commons": self.commons,"network": copy.copy(self.network), "funding_pool": 1000, "token_supply": 1000}, _input)
        proposals = get_proposals(
            self.network, status=ProposalStatus.CANDIDATE)

        proposal_ages = []
        proposal_thresholds = []
        for _, proposal in proposals:
            proposal_ages.append(proposal.age)
            proposal_thresholds.append(proposal.trigger)

        self.assertEqual(proposal_ages, [1, 1])
        self.assertEqual(proposal_thresholds, [np.inf, 2000.0])

    def test_su_calculate_conviction(self):
        """
        Ensure that conviction was calculated correctly

        After the 1st iteration, 100 tokens staked becomes 100 conviction

        On the 2nd iteration, 100 current tokens + 10
        days_to_80p_of_max_voting_weight * 100 prior conviction = 1100
        conviction
        """
        support_edges = get_edges_by_type(self.network, "support")
        for i, j in support_edges:
            self.network.edges[i, j]["tokens"] = 100

        n_0 = copy.copy(self.network)
        _, n_1 = ProposalFunding.su_calculate_conviction(
            self.params, 0, 0, {"network": n_0, "funding_pool": 1000, "token_supply": 1000}, {})
        # Make sure the conviction actually changed
        for i, j in support_edges:
            edge = n_1.edges[i, j]
            self.assertEqual(edge["tokens"], 100)
            self.assertEqual(edge["conviction"], 100)

        _, n_2 = ProposalFunding.su_calculate_conviction(
            self.params, 0, 0, {"network": copy.copy(n_1), "funding_pool": 1000, "token_supply": 1000}, {})
        for i, j in support_edges:
            edge = n_2.edges[i, j]
            self.assertEqual(edge["tokens"], 100)
            self.assertEqual(edge["conviction"], 1100)


class TestParticipantVoting(unittest.TestCase):
    def setUp(self):
        self.params = {
            "debug": False,
            "days_to_80p_of_max_voting_weight": 10,
            "probability_func": new_probability_func(seed=None),
            "exponential_func": new_exponential_func(seed=None),
            "gamma_func": new_gamma_func(seed=None),
            "random_number_func": new_random_number_func(seed=None)
        }
        self.network = bootstrap_network([TokenBatch(1000, 0, vesting_options=VestingOptions(10, 30))
                                          for _ in range(4)], 1, 3000, 4e6, 0.2, self.params["probability_func"],
                                          self.params["random_number_func"], self.params["gamma_func"],
                                          self.params["exponential_func"])

        self.network, _ = add_proposal(self.network, Proposal(100, 1), self.params["random_number_func"])

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
        self.params["probability_func"] = always
        ans = ParticipantVoting.p_participant_votes_on_proposal_according_to_affinity(
            self.params, 0, 0, {"network": copy.copy(self.network), "funding_pool": 1000, "token_supply": 1000})

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
            participant.holdings = TokenBatch(1000, 1000)

        self.params["probability_func"] = always
        ans = ParticipantVoting.p_participant_votes_on_proposal_according_to_affinity(
            self.params, 0, 0, {"network": copy.copy(self.network), "funding_pool": 1000, "token_supply": 1000})

        reference = {
            'participants_stake_on_proposals': {0: {4: 1000.0, 5: 1000.0},
                                                1: {4: 1000.0, 5: 1000.0},
                                                2: {4: 1000.0, 5: 1000.0},
                                                3: {4: 1000.0, 5: 1000.0}
                                                }
        }
        self.assertEqual(ans, reference)

    def test_su_update_participants_votes(self):
        """
        Test that the support edges with the new amount of tokens the
        Participant has staked on the Proposal are being updated.
        """
        network_copy = copy.copy(self.network)
        _input = {"participants_stake_on_proposals": {0: {4: 500.0, 5: 400.0}}}
        ParticipantVoting.su_update_participants_votes(
        self.params, 0, 0, {"network": network_copy, "funding_pool": 1000, "token_supply": 1000}, _input)

        self.assertEqual(network_copy[0][4]["tokens"], 500)
        self.assertEqual(network_copy[0][5]["tokens"], 400)


class TestParticipantBuysTokens(unittest.TestCase):
    def setUp(self):
        self.params = {
            "debug": True,
            "probability_func": new_probability_func(seed=None),
            "exponential_func": new_exponential_func(seed=None),
            "gamma_func": new_gamma_func(seed=None),
            "random_number_func": new_random_number_func(seed=None)
        }
        self.network = bootstrap_network([TokenBatch(1000, 1000, vesting_options=VestingOptions(10, 30))
                                          for _ in range(4)], 1, 3000, 4e6, 0.2, self.params["probability_func"],
                                          self.params["random_number_func"], self.params["gamma_func"],
                                          self.params["exponential_func"])
        self.commons = Commons(1000, 1000)

        self.network, _ = add_proposal(self.network, Proposal(100, 1), self.params["random_number_func"])
        self.default_state = {"network": self.network, "commons": self.commons,
                              "funding_pool": 1000, "token_supply": 1000}

    def test_p_decide_to_buy_tokens_bulk(self):
        with patch("entities.Participant.buy") as p:
            p.return_value = 1000.0
            a = ParticipantBuysTokens.p_decide_to_buy_tokens_bulk(
                self.params, 0, 0, self.default_state)
            decisions = a["participant_decisions"]
            final_token_distribution = a["final_token_distribution"]
            for participant_idx, decision in decisions.items():
                self.assertNotEqual(decision, 0)
                self.assertEqual(
                    final_token_distribution[participant_idx], 0.25)

    def test_p_decide_to_buy_tokens_bulk_no_tokens_bought(self):
        with patch("entities.Participant.buy") as p:
            p.return_value = 0.0
            a = ParticipantBuysTokens.p_decide_to_buy_tokens_bulk(
                self.params, 0, 0, self.default_state)

            expected = {"participant_decisions": {}, "total_dai": 0,
                        "tokens": 0, "token_price": 0, "final_token_distribution": {}}
            self.assertEqual(expected, a)

    def test_su_buy_participants_tokens(self):
        policy_result = {
            'participant_decisions': {0: 1000.0, 1: 1000.0, 2: 1000.0,
                                      3: 1000.0},
            'total_dai': 4000.0,
            'tokens': 1449.489742783178,
            'token_price': 2.7595917942265427,
            "final_token_distribution": {0: 0.25, 1: 0.25, 2: 0.25, 3: 0.25}
        }
        old_token_supply = self.commons._token_supply
        old_funding_pool = self.commons._funding_pool

        _, commons = ParticipantBuysTokens.su_buy_participants_tokens(
            self.params, 0, 0, self.default_state, policy_result)

        self.assertEqual(commons._token_supply, 2449.489742783178)
        self.assertEqual(commons._funding_pool, old_funding_pool)  # 200

    def test_su_buy_participants_tokens_zero(self):
        policy_result = {
            'participant_decisions': {},
            'total_dai': 0.0,
            'tokens': 0,
            'token_price': 0,
            "final_token_distribution": {}
        }
        old_token_supply = self.commons._token_supply
        old_funding_pool = self.commons._funding_pool

        _, commons = ParticipantBuysTokens.su_buy_participants_tokens(
            self.params, 0, 0, self.default_state, policy_result)

        self.assertEqual(commons._token_supply, old_token_supply)
        self.assertEqual(commons._funding_pool, old_funding_pool)

    def test_su_update_participants_tokens(self):
        policy_result = {
            'participant_decisions': {0: 1000.0, 1: 1000.0, 2: 1000.0,
                                      3: 1000.0},
            'total_dai': 4000.0,
            'tokens': 1449.489742783178,
            'token_price': 2.7595917942265427,
            "final_token_distribution": {0: 0.25, 1: 0.25, 2: 0.25, 3: 0.25}
        }
        _, network = ParticipantBuysTokens.su_update_participants_tokens(
            self.params, 0, 0, self.default_state, policy_result)

        for i in [0, 1, 2, 3]:
            self.assertEqual(
                network.nodes[i]["item"].holdings.nonvesting, 1362.3724356957946)


class TestParticipantSellsTokens(unittest.TestCase):
    def setUp(self):
        self.params = {
            "debug": False,
            "probability_func": new_probability_func(seed=None),
            "exponential_func": new_exponential_func(seed=None),
            "gamma_func": new_gamma_func(seed=None),
            "random_number_func": new_random_number_func(seed=None)
        }
        self.network = bootstrap_network([TokenBatch(1000, 1000, vesting_options=VestingOptions(10, 30))
                                          for _ in range(4)], 1, 3000, 4e6, 0.2, self.params["probability_func"],
                                          self.params["random_number_func"], self.params["gamma_func"],
                                          self.params["exponential_func"])
        self.commons = Commons(1000, 1000)

        self.network, _ = add_proposal(self.network, Proposal(100, 1), self.params["random_number_func"])
        self.default_state = {"network": self.network, "commons": self.commons,
                              "funding_pool": 1000, "token_supply": 1000}

    def test_p_decide_to_sell_tokens_bulk(self):
        with patch("entities.Participant.sell") as p:
            p.return_value = 20.0
            a = ParticipantSellsTokens.p_decide_to_sell_tokens_bulk(
                self.params, 0, 0, self.default_state)

            expected_a = {
                'participant_decisions': {0: 20.0, 1: 20.0, 2: 20.0, 3: 20.0},
                'total_tokens': 80.0,
                'dai_returned': 122.88,
                'realized_price': 1.536,
            }

            self.assertEqual(a, expected_a)

    def test_p_decide_to_sell_tokens_bulk_no_tokens_sold(self):
        with patch("entities.Participant.sell") as p:
            p.return_value = 0.0
            a = ParticipantSellsTokens.p_decide_to_sell_tokens_bulk(
                self.params, 0, 0, self.default_state)

            expected = {"participant_decisions": {},
                        "total_tokens": 0, "dai_returned": 0, "realized_price": 0}
            self.assertEqual(expected, a)

    def test_su_burn_participants_tokens(self):
        policy_result = {
            'participant_decisions': {0: 20.0, 1: 20.0, 2: 20.0, 3: 20.0},
            'total_tokens': 80.0,
            'dai_returned': 122.88,
            'realized_price': 1.536,
        }
        old_token_supply = self.commons._token_supply
        old_funding_pool = self.commons._funding_pool

        _, commons = ParticipantSellsTokens.su_burn_participants_tokens(
            self.params, 0, 0, self.default_state, policy_result)

        self.assertEqual(commons._token_supply, 920.0)
        self.assertEqual(commons._funding_pool, old_funding_pool)  # 200

    def test_su_sell_participants_tokens_zero(self):
        policy_result = {
            'participant_decisions': {},
            'total_tokens': 0.0,
            'dai_returned': 0,
            'realized_price': 0,
        }
        old_token_supply = self.commons._token_supply
        old_funding_pool = self.commons._funding_pool

        _, commons = ParticipantSellsTokens.su_burn_participants_tokens(
            self.params, 0, 0, self.default_state, policy_result)

        self.assertEqual(commons._token_supply, old_token_supply)
        self.assertEqual(commons._funding_pool, old_funding_pool)

    def test_su_update_participants_tokens(self):
        policy_result = {
            'participant_decisions': {0: 20.0, 1: 20.0, 2: 20.0, 3: 20.0},
            'total_tokens': 80.0,
            'dai_returned': 122.88,
            'realized_price': 1.536,
        }
        _, network = ParticipantSellsTokens.su_update_participants_tokens(
            self.params, 0, 0, self.default_state, policy_result)

        for i in [0, 1, 2, 3]:
            self.assertEqual(
                network.nodes[i]["item"].holdings.nonvesting, 980.0)


class TestParticipantExits(unittest.TestCase):
    def setUp(self):
        self.params = {
            "debug": True,
            "probability_func": new_probability_func(seed=None),
            "exponential_func": new_exponential_func(seed=None),
            "gamma_func": new_gamma_func(seed=None),
            "random_number_func": new_random_number_func(seed=None)
        }
        self.network = bootstrap_network([TokenBatch(1000, 1000, vesting_options=VestingOptions(10, 30))
                                          for _ in range(4)], 1, 3000, 4e6, 0.2, self.params["probability_func"],
                                          self.params["random_number_func"], self.params["gamma_func"],
                                          self.params["exponential_func"])
        self.commons = Commons(1000, 1000)

        self.network, _ = add_proposal(self.network, Proposal(100, 1), self.params["random_number_func"])
        self.default_state = {"network": self.network, "commons": self.commons,
                              "funding_pool": 1000, "token_supply": 1000}

    def test_p_participant_decides_if_he_wants_to_exit(self):
        participants = get_participants(self.network)
        for i, participant in participants:
            participant.sentiment = 0.1

        self.params["probability_func"] = always
        ans = ParticipantExits.p_participant_decides_if_he_wants_to_exit(
            self.params, 0, 0, self.default_state)

        self.assertEqual(len(ans["defectors"]), 4)

    def test_su_remove_participants_from_network(self):
        policy_output = {
            "defectors": {
                1: {
                    "sentiment": 0.1,
                    "holdings": 10000,
                },
                2: {
                    "sentiment": 0.1,
                    "holdings": 10000,
                }
            }
        }

        _, n_network = ParticipantExits.su_remove_participants_from_network(
            self.params, 0, 0, self.default_state, policy_output)

        with self.assertRaises(nx.NetworkXError):
            n_network.remove_node(1)
            n_network.remove_node(2)

    def test_su_burn_exiters_tokens(self):
        policy_output = {
            "defectors": {
                1: {
                    "sentiment": 0.1,
                    "holdings": 10000,
                },
                2: {
                    "sentiment": 0.1,
                    "holdings": 10000,
                }
            }
        }
        old_collateral_pool = self.commons._collateral_pool
        old_token_supply = self.commons._token_supply
        _, n_commons = ParticipantExits.su_burn_exiters_tokens(
            self.params, 0, 0, self.default_state, policy_output)

        self.assertNotEqual(old_collateral_pool, n_commons._collateral_pool)
        self.assertNotEqual(old_token_supply, n_commons._token_supply)

    def test_su_update_sentiment_when_proposal_becomes_active(self):
        """
        Because this policy depends on a policy passthrough from a previous
        partial state update block, it does not use _input, but
        s["policy_output"]
        """
        policy_output_passthru = {
            "proposal_idxs_with_enough_conviction": [4, 5]
        }

        # Let's say Participant 2 owns Proposal 4, Participant 3 owns Proposal 5
        self.network.nodes[2]["item"].sentiment = 0.4
        self.network.nodes[3]["item"].sentiment = 0.6
        self.network.edges[2, 4]["affinity"] = 1
        self.network.edges[3, 5]["affinity"] = 1

        self.default_state["policy_output"] = policy_output_passthru
        _, n_network = ParticipantExits.su_update_sentiment_when_proposal_becomes_active(
            self.params, 0, 0, self.default_state, {})

        self.assertEqual(n_network.nodes[2]["item"].sentiment, 0.9)
        self.assertEqual(n_network.nodes[3]["item"].sentiment, 1)

    def test_su_update_sentiment_when_proposal_becomes_failed_or_completed(self):
        """
        Because this policy depends on a policy passthrough from a previous
        partial state update block, it does not use _input, but
        s["policy_output"]
        """
        policy_output_passthru = {
            "failed": [4],
            "succeeded": [5]
        }

        # Let's say Participant 2 owns Proposal 4, Participant 3 owns Proposal 5
        self.network.nodes[2]["item"].sentiment = 0.5
        self.network.nodes[3]["item"].sentiment = 0.7
        self.network.edges[2, 4]["affinity"] = 1
        self.network.edges[3, 5]["affinity"] = 1

        self.default_state["policy_output"] = policy_output_passthru
        _, n_network = ParticipantExits.su_update_sentiment_when_proposal_becomes_failed_or_completed(
            self.params, 0, 0, self.default_state, {})

        self.assertEqual(n_network.nodes[2]["item"].sentiment, 0.4)
        self.assertEqual(n_network.nodes[3]["item"].sentiment, 1)
