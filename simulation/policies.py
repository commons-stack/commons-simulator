import config
import random
import copy
import numpy as np
from scipy.stats import expon, gamma

from convictionvoting import trigger_threshold
from entities import Participant, Proposal, ProposalStatus
from hatch import TokenBatch
from network_utils import (add_proposal, add_participant, calc_median_affinity, calc_total_conviction,
                           calc_total_funds_requested, find_in_edges_of_type_for_proposal, get_edges_by_type,
                           get_participants, get_proposals,
                           setup_influence_edges_single, setup_support_edges)
from utils import probability


class GenerateNewParticipant:
    @staticmethod
    def p_randomly(params, step, sL, s, **kwargs):
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
    def su_add_to_network(params, step, sL, s, _input, **kwargs):
        network = s["network"]
        if _input["new_participant"]:
            network, i = add_participant(network, Participant(TokenBatch(
                0, _input["new_participant_tokens"])))

            if params.get("debug"):
                print("GenerateNewParticipant: A new Participant {} invested {}DAI for {} tokens".format(
                    i, _input['new_participant_investment'], _input['new_participant_tokens']))
        return "network", network

    @staticmethod
    def su_add_investment_to_commons(params, step, sL, s, _input, **kwargs):
        commons = s["commons"]
        if _input["new_participant"]:
            tokens, realized_price = commons.deposit(
                _input["new_participant_investment"])
        return "commons", commons


class GenerateNewProposal:
    @staticmethod
    def p_randomly(params, step, sL, s, **kwargs):
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
    def su_add_to_network(params, step, sL, s, _input, **kwargs):
        network = s["network"]
        funding_pool = s["funding_pool"]
        token_supply = s["token_supply"]
        scale_factor = 0.01
        if _input["new_proposal"]:
            # Create the Proposal and add it to the network.
            rescale = funding_pool * scale_factor
            r_rv = gamma.rvs(3, loc=0.001, scale=rescale)
            proposal = Proposal(funds_requested=r_rv,
                                trigger=trigger_threshold(r_rv, funding_pool, token_supply, params["max_proposal_request"]))
            network, proposal_idx = add_proposal(network, proposal)

            # add_proposal() has created support edges from other Participants
            # to this Proposal. If the Participant is the one who created this
            # Proposal, change his affinity for the Proposal to 1 (maximum).
            network.edges[_input["proposed_by_participant"],
                          proposal_idx]["affinity"] = 1
            if params.get("debug"):
                print("GenerateNewProposal: Participant {} created Proposal {}".format(
                    _input["proposed_by_participant"], proposal_idx))
        return "network", network


class GenerateNewFunding:
    @staticmethod
    def p_exit_tribute_of_average_speculator_position_size(params, step, sL, s, **kwargs):
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
    def su_add_funding(params, step, sL, s, _input, **kwargs):
        commons = s["commons"]
        if _input["funding"]:
            commons._funding_pool += _input["funding"]
        return "commons", commons


class ActiveProposals:
    @staticmethod
    def p_influenced_by_grant_size(params, step, sL, s, **kwargs):
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

    @staticmethod
    def su_set_proposal_status(params, step, sL, s, _input, **kwargs):
        network = s["network"]
        for idx in _input["failed"]:
            network.nodes[idx]["item"].status = ProposalStatus.FAILED

        for idx in _input["succeeded"]:
            network.nodes[idx]["item"].status = ProposalStatus.COMPLETED

        return "network", network


class ProposalFunding:
    @staticmethod
    def p_compare_conviction_and_threshold(params, step, sL, s, **kwargs):
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
            total_conviction = calc_total_conviction(network, idx)
            proposal.conviction = total_conviction
            res = proposal.has_enough_conviction(
                funding_pool, token_supply, params["max_proposal_request"])

            if params.get("debug"):
                print("ProposalFunding: Proposal {} has {} conviction, and needs {} to pass".format(idx,
                                                                                                    proposal.conviction, proposal.trigger))
            if res:
                proposals_w_enough_conviction.append(idx)

        return {"proposal_idxs_with_enough_conviction": proposals_w_enough_conviction}

    @staticmethod
    def su_make_proposal_active(params, step, sL, s, _input, **kwargs):
        network = s["network"]

        for idx in _input["proposal_idxs_with_enough_conviction"]:
            network.nodes[idx]["item"].status = ProposalStatus.ACTIVE

        return "network", network

    @staticmethod
    def su_deduct_funds_from_funding_pool(params, step, sL, s, _input, **kwargs):
        commons = s["commons"]
        network = s["network"]
        for idx in _input["proposal_idxs_with_enough_conviction"]:
            funds = network.nodes[idx]["item"].funds_requested
            if params.get("debug"):
                print("ProposalFunding: Proposal {} passed! deducting {} from Commons funding pool".format(
                    idx, funds))
            commons.spend(funds)
        return "commons", commons

    @staticmethod
    def su_update_age_and_conviction_thresholds(params, step, sL, s, _input, **kwargs):
        network = s["network"]
        funding_pool = s["funding_pool"]
        token_supply = s["token_supply"]

        proposals = get_proposals(
            s["network"], status=ProposalStatus.CANDIDATE)
        for _, proposal in proposals:
            proposal.update_age()
            proposal.update_threshold(
                funding_pool, token_supply, max_proposal_request=params["max_proposal_request"])

        return "network", network

    @staticmethod
    def su_calculate_conviction(params, step, sL, s, _input, **kwargs):
        """
        Actually calculates the conviction. This function should only run ONCE
        per timestep/iteration!
        """
        network = s["network"]
        alpha = params["alpha_days_to_80p_of_max_voting_weight"]

        support_edges = get_edges_by_type(network, "support")
        for i, j in support_edges:
            edge = network.edges[i, j]
            prior_conviction = edge['conviction']
            current_tokens = edge['tokens']

            edge['conviction'] = current_tokens + alpha*prior_conviction
            if params.get("debug") and s["timestep"] == 1:
                print("ProposalFunding: Participant {} initially has staked {} tokens on Proposal {}, which will result in {} conviction in the next timestep".format(
                    i, current_tokens, j, edge["conviction"]))

        return "network", network


class ParticipantVoting:
    @staticmethod
    def p_participant_votes_on_proposal_according_to_affinity(params, step, sL, s, **kwargs):
        """
        This policy collects data from the DiGraph to tell the Participant class
        which candidate proposals it supports, and
        Participant.vote_on_candidate_proposals() will decide which proposals it
        will take action on.

        Then, Participant.stake_across_all_supported_proposals() will tell us
        how much it will stake on each of them.
        """
        network = s["network"]
        participants = get_participants(network)
        candidate_proposals = get_proposals(
            network, status=ProposalStatus.CANDIDATE)

        participants_stakes = {}
        for participant_idx, participant in participants:
            proposal_idx_affinity = {}  # {4: 0.9, 5: 0.9}
            for proposal_idx, _ in candidate_proposals:
                proposal_idx_affinity[proposal_idx] = network[participant_idx][proposal_idx]["affinity"]
            proposals_that_participant_cares_enough_to_vote_on = participant.vote_on_candidate_proposals(
                proposal_idx_affinity)

            stake_across_all_supported_proposals_input = []
            for proposal_idx, affinity in proposals_that_participant_cares_enough_to_vote_on.items():
                stake_across_all_supported_proposals_input.append(
                    (affinity, proposal_idx))
            stakes = participant.stake_across_all_supported_proposals(
                stake_across_all_supported_proposals_input)

            participants_stakes[participant_idx] = stakes

            if params.get("debug"):
                if proposals_that_participant_cares_enough_to_vote_on:
                    print("ParticipantVoting: Participant {} was given Proposals with corresponding affinities {} and he decided to vote on {}, distributing his tokens thusly {}".format(
                        participant_idx, proposal_idx_affinity, proposals_that_participant_cares_enough_to_vote_on, stakes))

        return {"participants_stake_on_proposals": participants_stakes}

    @staticmethod
    def su_update_participants_votes(params, step, sL, s, _input, **kwargs):
        """
        Simply update the support edges with the new amount of tokens the
        Participant has staked on the Proposal. Leave the conviction calculation
        to another state update function.
        """
        network = s["network"]
        _input = _input["participants_stake_on_proposals"]

        for participant_idx, v in _input.items():
            for proposal_idx, tokens_staked in v.items():
                # I assume there is no longer a need to recalculate a la
                # https://github.com/randomshinichi/conviction/blob/9d1bc9513475dc30d33e3232b385234d0295d361/conviction_system_logic3.py#L510
                # because the tokens were already distributed proportionally to
                # the affinities in
                # p_participant_votes_on_proposal_according_to_affinity()
                # Also, do not recalculate conviction here. Leave that to ProposalFunding.su_calculate_conviction()
                network[participant_idx][proposal_idx]["tokens"] = tokens_staked

        return "network", network


class ParticipantBuysTokens:
    """
    When implementing buying tokens, Participants may either buy in bulk with no
    slippage, or endure slippage while buying. Neither is realistic but I'd say
    no slippage is closer to what Participants will experience in real life.

    When implementing selling tokens, slippage is more likely to change the
    decision. In any case, let us implement no slippage first since it is easier
    to reason with.

    Also, buying in bulk is easier to implement in cadCAD because if the state
    update function changes the Commons object each time a Participant buys
    in/sells out, then it would have to update the network and commons object in
    the same function, which is not allowed in cadCAD.
    """
    @staticmethod
    def p_decide_to_buy_tokens_bulk(params, step, sL, s, **kwargs):
        network = s["network"]
        commons = s["commons"]
        participants = get_participants(network)
        ans = {}
        total_dai = 0
        for i, participant in participants:
            # If a participant decides to buy, it will be specified in units of DAI.
            # If a participant decides to sell, it will be specified in units of tokens.
            x = participant.buy()
            if x > 0:
                total_dai += x
                ans[i] = x

        # Now that we have the sum of DAI, ask the Commons object how many
        # tokens this would be minted as a result. This will be inaccurate due
        # to slippage, and we need the result of this policy to be final to
        # avoid chaining 2 state update functions, so we run the deposit on a
        # throwaway copy of Commons
        if total_dai == 0:
            if params.get("debug"):
                print(
                    "ParticipantBuysTokens: No Participants bought tokens in timestep {}".format(step))
            return {"participant_decisions": ans, "total_dai": 0, "tokens": 0, "token_price": 0, "final_token_distribution": {}}

        else:
            commons2 = copy.copy(commons)
            tokens, token_price = commons2.deposit(total_dai)

            final_token_distribution = {}
            for i in ans:
                final_token_distribution[i] = ans[i] / total_dai

            if params.get("debug"):
                print(
                    "ParticipantBuysTokens: These Participants have decided to buy tokens with this amount of DAI: {}".format(ans))
                print("ParticipantBuysTokens: A total of {} DAI will be deposited. {} tokens should be minted as a result at a price of {} DAI/token".format(
                    total_dai, tokens, token_price))

            return {"participant_decisions": ans, "total_dai": total_dai, "tokens": tokens, "token_price": token_price, "final_token_distribution": final_token_distribution}

    @staticmethod
    def su_buy_participants_tokens(params, step, sL, s, _input, **kwargs):
        commons = s["commons"]

        if _input["total_dai"] > 0:
            tokens, realized_price = commons.deposit(_input["total_dai"])
            if _input["tokens"] != tokens or _input["token_price"] != realized_price:
                raise Exception("ParticipantBuysTokens: {} tokens were minted at a price of {} (expected: {} with price {})".format(
                    tokens, realized_price, _input["tokens"], _input["token_price"]))

        return "commons", commons

    @staticmethod
    def su_update_participants_tokens(params, step, sL, s, _input, **kwargs):
        network = s["network"]
        decisions = _input["participant_decisions"]
        final_token_distribution = _input["final_token_distribution"]
        tokens = _input["tokens"]

        for participant_idx, decision in decisions.items():
            network.nodes[participant_idx]["item"].increase_holdings(
                final_token_distribution[participant_idx] * tokens)

        return "network", network


class ParticipantSellsTokens:
    @staticmethod
    def p_decide_to_sell_tokens_bulk(params, step, sL, s, **kwargs):
        network = s["network"]
        commons = s["commons"]
        participants = get_participants(network)
        ans = {}
        total_tokens = 0
        for i, participant in participants:
            # If a participant decides to buy, it will be specified in units of DAI.
            # If a participant decides to sell, it will be specified in units of tokens.
            x = participant.sell()
            if x > 0:
                total_tokens += x
                ans[i] = x

        # Now that we have the sum of tokens, ask the Commons object how many
        # DAI would be redeemed as a result. This will be inaccurate due
        # to slippage, and we need the result of this policy to be final to
        # avoid chaining 2 state update functions, so we run the operation on a
        # throwaway copy of Commons
        if total_tokens == 0:
            if params.get("debug"):
                print(
                    "ParticipantSellsTokens: No Participants sold tokens in timestep {}".format(step))
            return {"participant_decisions": ans, "total_tokens": 0, "dai_returned": 0, "realized_price": 0}
        else:
            commons2 = copy.copy(commons)
            dai_returned, realized_price = commons2.burn(total_tokens)

            final_dai_distribution = {}
            for i, participant in participants:
                final_dai_distribution[i] = ans[i] / total_tokens

            if params.get("debug"):
                print(
                    "ParticipantSellsTokens: These Participants have decided to sell this many  tokens: {}".format(ans))
                print("ParticipantSellsTokens: A total of {} tokens will be burned. {} DAI should be returned as a result, at a price of {} DAI/token".format(
                    total_tokens, dai_returned, realized_price))
            return {"participant_decisions": ans, "total_tokens": total_tokens, "dai_returned": dai_returned, "realized_price": realized_price}

    @staticmethod
    def su_burn_participants_tokens(params, step, sL, s, _input, **kwargs):
        commons = s["commons"]

        if _input["total_tokens"] > 0:
            dai_returned, realized_price = commons.burn(_input["total_tokens"])
            if _input["dai_returned"] != dai_returned or _input["realized_price"] != realized_price:
                raise Exception("ParticipantSellsTokens: {} DAI was returned at a price of {} (expected: {} with price {})".format(
                    dai_returned, realized_price, _input["dai_returned"], _input["realized_price"]))

        return "commons", commons

    @staticmethod
    def su_update_participants_tokens(params, step, sL, s, _input, **kwargs):
        network = s["network"]
        decisions = _input["participant_decisions"]
        dai_returned = _input["dai_returned"]

        for participant_idx, decision in decisions.items():
            network.nodes[participant_idx]["item"].spend(decision)

        return "network", network


class ParticipantExits:
    @staticmethod
    def p_participant_decides_if_he_wants_to_exit(params, step, sL, s, **kwargs):
        network = s["network"]
        participants = get_participants(network)
        defectors = {}
        for i, participant in participants:
            e = participant.wants_to_exit()
            if e:
                defectors[i] = {
                    "sentiment": participant.sentiment,
                    "holdings": participant.holdings.total,
                }

        if params.get("debug"):
            print("ParticipantExits: Participants {} (2nd number is their sentiment) want to exit".format(
                defectors))
        return {"defectors": defectors}

    @staticmethod
    def su_remove_participants_from_network(params, step, sL, s, _input, **kwargs):
        network = s["network"]
        defectors = _input["defectors"]

        for i, _ in defectors.items():
            network.remove_node(i)

        return "network", network

    @staticmethod
    def su_burn_exiters_tokens(params, step, sL, s, _input, **kwargs):
        commons = s["commons"]
        network = s["network"]
        defectors = _input["defectors"]

        burnt_token_results = {}
        for i, v in defectors.items():
            dai_returned, realized_price = commons.burn(v["holdings"])
            burnt_token_results[i] = {
                "dai_returned": dai_returned, "realized_price": realized_price}

        return "commons", commons

    @staticmethod
    def su_update_sentiment_when_proposal_becomes_active(params, step, sL, s, _input, **kwargs):
        network = s["network"]
        policy_output_passthru = s["policy_output"]

        report = {}
        for idx in policy_output_passthru["proposal_idxs_with_enough_conviction"]:
            for participant_idx, proposal_idx, _ in find_in_edges_of_type_for_proposal(network, idx, "support"):
                edge = network.edges[participant_idx, proposal_idx]
                if edge["affinity"] == 1:
                    sentiment_old = network.nodes[participant_idx]["item"].sentiment
                    sentiment_new = sentiment_old + config.sentiment_bonus_proposal_becomes_active
                    sentiment_new = 1 if sentiment_new > 1 else sentiment_new
                    network.nodes[participant_idx]["item"].sentiment = sentiment_new

                    report[participant_idx] = {
                        "proposal_idx": proposal_idx,
                        "sentiment_old": sentiment_old,
                        "sentiment_new": sentiment_new
                    }

        if params.get("debug"):
            for i in report:
                print(
                    "ParticipantExits: Participant {} changed his sentiment from {} to {} because Proposal {} became active".format(i, report[i]["sentiment_old"], report[i]["sentiment_new"], report[i]["proposal_idx"]))
        return "network", network

    @staticmethod
    def su_update_sentiment_when_proposal_becomes_failed_or_completed(params, step, sL, s, _input, **kwargs):
        network = s["network"]
        policy_output_passthru = s["policy_output"]

        report = {}
        for idx in policy_output_passthru["failed"]:
            for participant_idx, proposal_idx, _ in find_in_edges_of_type_for_proposal(network, idx, "support"):
                edge = network.edges[participant_idx, proposal_idx]
                if edge["affinity"] == 1:
                    sentiment_old = network.nodes[participant_idx]["item"].sentiment
                    sentiment_new = sentiment_old + config.sentiment_bonus_proposal_becomes_failed
                    sentiment_new = 0 if sentiment_new < 0 else sentiment_new
                    network.nodes[participant_idx]["item"].sentiment = sentiment_new

                    report[participant_idx] = {
                        "proposal_idx": proposal_idx,
                        "sentiment_old": sentiment_old,
                        "sentiment_new": sentiment_new,
                        "status": "failed"
                    }
        
        for idx in policy_output_passthru["succeeded"]:
            for participant_idx, proposal_idx, _ in find_in_edges_of_type_for_proposal(network, idx, "support"):
                edge = network.edges[participant_idx, proposal_idx]
                if edge["affinity"] == 1:
                    sentiment_old = network.nodes[participant_idx]["item"].sentiment
                    sentiment_new = sentiment_old + config.sentiment_bonus_proposal_becomes_completed
                    sentiment_new = 1 if sentiment_new > 1 else sentiment_new
                    network.nodes[participant_idx]["item"].sentiment = sentiment_new

                    report[participant_idx] = {
                        "proposal_idx": proposal_idx,
                        "sentiment_old": sentiment_old,
                        "sentiment_new": sentiment_new,
                        "status": "completed"
                    }
        
        if params.get("debug"):
            for i in report:
                print(
                    "ParticipantExits: Participant {} changed his sentiment from {} to {} because Proposal {} became {}".format(i, report[i]["sentiment_old"], report[i]["sentiment_new"], report[i]["proposal_idx"], report[i]["status"]))
        return "network", network
