import random

import numpy as np
from scipy.stats import expon, gamma

import convictionvoting
from entities import Participant, Proposal, ProposalStatus
from hatch import TokenBatch
from network_utils import (add_proposal, calc_median_affinity,
                           calc_total_funds_requested, get_participants, get_edges_by_type,
                           get_proposals, setup_influence_edges_single,
                           setup_support_edges)
from utils import probability


class GenerateNewParticipant:
    @staticmethod
    def p_randomly(params, step, sL, s):
        commons = s["commons"]
        sentiment = s["sentiment"]
        ans = {
            "new_participant": False,
            "new_participant_investment": None,
            "new_participant_tokens": None
        }

        arrival_rate = (1+sentiment)/10
        if probability(arrival_rate):
            ans["new_participant"] = True
            # Here we randomly generate each participant's post-Hatch
            # investment, in DAI/USD.
            #
            # expon.rvs() arguments:
            #
            # loc is the minimum number, so if loc=100, there will be no
            # investments < 100
            #
            # scale is the standard deviation, so if scale=2, investments will
            # be around 0-12 DAI or even 15, if scale=100, the investments will be
            # around 0-600 DAI.
            ans["new_participant_investment"] = expon.rvs(loc=0.0, scale=100)
            ans["new_participant_tokens"] = commons.dai_to_tokens(
                ans["new_participant_investment"])
        return ans

    @staticmethod
    def su_add_to_network(params, step, sL, s, _input):
        network = s["network"]
        if _input["new_participant"]:
            i = len(network.nodes)
            network.add_node(i, item=Participant(
                holdings_vesting=None, holdings_nonvesting=TokenBatch(_input["new_participant_tokens"])))
            network = setup_influence_edges_single(network, i)
            network = setup_support_edges(network, i)
        return "network", network

    @staticmethod
    def su_add_investment_to_commons(params, step, sL, s, _input):
        commons = s["commons"]
        if _input["new_participant"]:
            tokens, realized_price = commons.deposit(
                _input["new_participant_investment"])
            # print(tokens, realized_price, _input['new_participant_tokens'])

        return "commons", commons


class GenerateNewProposal:
    @staticmethod
    def p_randomly(params, step, sL, s):
        """
        Randomly picks a Participant from the network and asks him if he wants
        to create a Proposal.
        """
        funding_pool = s["funding_pool"]
        network = s["network"]

        participants = get_participants(network)
        i, participant = random.sample(participants, 1)[0]

        wants_to_create_proposal = participant.create_proposal(calc_total_funds_requested(
            network), calc_median_affinity(network), funding_pool)

        return {"new_proposal": wants_to_create_proposal, "proposed_by_participant": i}

    @staticmethod
    def su_add_to_network(params, step, sL, s, _input):
        network = s["network"]
        funding_pool = s["funding_pool"]
        token_supply = s["token_supply"]
        scale_factor = 0.01
        if _input["new_proposal"]:
            # Create the Proposal and add it to the network.
            rescale = funding_pool * scale_factor
            r_rv = gamma.rvs(3, loc=0.001, scale=rescale)
            proposal = Proposal(funds_requested=r_rv,
                                trigger=convictionvoting.trigger_threshold(r_rv, funding_pool, token_supply))
            network, j = add_proposal(network, proposal)

            # add_proposal() has created support edges from other Participants
            # to this Proposal. If the Participant is the one who created this
            # Proposal, change his affinity for the Proposal to 1 (maximum).
            network.edges[_input["proposed_by_participant"], j]["affinity"] = 1
        return "network", network


class GenerateNewFunding:
    @staticmethod
    def p_exit_tribute_of_average_speculator_position_size(params, step, sL, s):
        """
        This policy needs Commons.exit_tribute to NOT be 0!

        TODO: buy tokens and sell them immediately within the same simulation
        step, assuming a certain position size.
        """
        speculator_position_size_min = 200  # DAI
        speculator_position_size_stdev = 200
        speculators = 5
        exits = [expon.rvs(loc=speculator_position_size_min,
                           scale=speculator_position_size_stdev) for i in range(speculators)]
        commons = s["commons"]
        funding = sum(exits) * commons.exit_tribute
        return {"funding": funding}

    @staticmethod
    def su_add_funding(params, step, sL, s, _input):
        commons = s["commons"]
        if _input["funding"]:
            commons._funding_pool += _input["funding"]
        return "commons", commons


class ActiveProposals:
    @staticmethod
    def p_influenced_by_grant_size(params, step, sL, s):
        base_failure_rate = 0.15
        base_success_rate = 0.30

        network = s["network"]

        active_proposals = get_proposals(network, status=ProposalStatus.ACTIVE)
        proposals_that_will_fail = []
        proposals_that_will_succeed = []

        for idx, proposal in active_proposals:
            r_failure = 1/(base_failure_rate +
                           np.log(proposal.funds_requested))
            r_success = 1/(base_success_rate +
                           np.log(proposal.funds_requested))
            if probability(r_failure):
                proposals_that_will_fail.append(idx)
            elif probability(r_success):
                proposals_that_will_succeed.append(idx)
        return {"failed": proposals_that_will_fail, "succeeded": proposals_that_will_succeed}

    @ staticmethod
    def su_set_proposal_status(params, step, sL, s, _input):
        network = s["network"]
        for idx in _input["failed"]:
            network.nodes[idx]["item"].status = ProposalStatus.FAILED

        return "network", network


class ProposalFunding:
    @staticmethod
    def p_compare_conviction_and_threshold(params, step, sL, s):
        """
        This policy simply goes through the Proposals to see if their thresholds
        are smaller than their gathered conviction
        """
        network = s["network"]
        funding_pool = s["funding_pool"]
        token_supply = s["token_supply"]

        proposals_w_enough_conviction = []
        proposals = get_proposals(network, status=ProposalStatus.CANDIDATE)
        for idx, proposal in proposals:
            res = proposal.has_enough_conviction(funding_pool, token_supply)
            if res:
                proposals_w_enough_conviction.append(idx)

        return {"has_enough_conviction": proposals_w_enough_conviction}

    @staticmethod
    def su_compare_conviction_and_threshold_make_proposal_active(params, step, sL, s, _input):
        network = s["network"]
        funding_pool = s["funding_pool"]
        token_supply = s["token_supply"]

        for idx in _input["has_enough_conviction"]:
            network[idx]["item"].status = ProposalStatus.ACTIVE

        return "network", network

    @staticmethod
    def su_update_age_and_conviction_thresholds(params, step, sL, s, _input):
        network = s["network"]
        funding_pool = s["funding_pool"]
        token_supply = s["token_supply"]

        proposals = get_proposals(
            s["network"], status=ProposalStatus.CANDIDATE)
        for proposal in proposals:
            proposal.update_age()
            proposal.update_threshold(funding_pool, token_supply)

        return "network", network

    @staticmethod
    def su_calculate_gathered_conviction(params, step, sL, s, _input):
        network = s["network"]

        participants = get_participants(network)
        proposals = get_proposals(network, status=ProposalStatus.CANDIDATE)
        support_edges = get_edges_by_type(network, "support")
        total_affinity = np.sum(
            [network.edges[(i, j)]['affinity'] for i, j in support_edges])

        for i, j in support_edges:
            participant = network.nodes[i]["item"]
            normalized_affinity = network.edges[i,
                                                j]["affinity"]/total_affinity
            network.edges[i, j]["tokens"] = normalized_affinity * \
                participant.holdings

            prior_conviction = network.edges[i, j]['conviction']
            current_tokens = network.edges[i, j]['tokens']

            network.edges[i, j]['conviction'] = current_tokens + \
                days_to_80p_of_max_voting_weight*prior_conviction

        return "network", network
