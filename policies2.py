import random
from scipy.stats import expon, gamma

from entities import Participant, Proposal
from hatch import TokenBatch
from network_utils import (calc_median_affinity, calc_total_funds_requested,
                           get_participants, setup_influence_edges,
                           setup_support_edges)
from utils import probability
import convictionvoting


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
            network = setup_influence_edges(network, i)
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
        i = random.choice(participants)
        wants_to_create_proposal = participants[i].create_proposal(calc_total_funds_requested(
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
            j = len(network.nodes)
            rescale = funding_pool * scale_factor
            r_rv = gamma.rvs(3, loc=0.001, scale=rescale)
            proposal = Proposal(funds_requested=r_rv,
                        trigger=convictionvoting.trigger_threshold(r_rv, funding_pool, token_supply))
            network.add_node(j, item=proposal)

            # Create support edges from Participants to this Proposal. If
            # the Participant is the one who created this Proposal, his affinity
            # for the Proposal is 1 (maximum).
            network = setup_support_edges(network, j)
            network.edges[_input["proposed_by_participant"], j]["affinity"] = 1
        return "network", network
