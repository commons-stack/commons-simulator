import numpy as np
from hatch import create_token_batches, TokenBatch, Commons

from entities import attrs
from policies import GenerateNewParticipant, GenerateNewProposal, GenerateNewFunding, ActiveProposals, ProposalFunding, ParticipantVoting, ParticipantSellsTokens, ParticipantBuysTokens, ParticipantExits
from network_utils import bootstrap_network, calc_avg_sentiment


def update_collateral_pool(params, step, sL, s, _input):
    commons = s["commons"]
    s["collateral_pool"] = commons._collateral_pool
    return "collateral_pool", commons._collateral_pool


def update_token_supply(params, step, sL, s, _input):
    commons = s["commons"]
    s["token_supply"] = commons._token_supply
    return "token_supply", commons._token_supply


def update_funding_pool(params, step, sL, s, _input):
    commons = s["commons"]
    s["funding_pool"] = commons._funding_pool
    return "funding_pool", commons._funding_pool


def update_avg_sentiment(params, step, sL, s, _input):
    network = s["network"]
    s = calc_avg_sentiment(network)
    return "sentiment", s


def save_policy_output(params, step, sL, s, _input):
    return "policy_output", _input


# This sub-policy block should be run every time the Commons object is updated.
sync_state_variables = {
    "policies": {},
    "variables": {
        "funding_pool": update_funding_pool,
        "collateral_pool": update_collateral_pool,
        "token_supply": update_token_supply,
        "sentiment": update_avg_sentiment,
    }
}


class CommonsSimulationConfiguration:
    """
    There are just so many options that passing them via kwargs has become
    rather unwieldy. Also it would be useful to have some footnotes next to each
    parameter.
    """

    def __init__(self,
                 hatchers=5,
                 proposals=2,
                 hatch_tribute=0.2,
                 vesting_80p_unlocked=60,
                 exit_tribute=0.35,
                 kappa=2,
                 days_to_80p_of_max_voting_weight=10,
                 max_proposal_request=0.2):
        self.hatchers = hatchers
        self.proposals = proposals
        self.hatch_tribute = hatch_tribute

        # 60 is 2 months until 80% of tokens are unlocked
        self.vesting_80p_unlocked = vesting_80p_unlocked
        self.exit_tribute = exit_tribute
        self.kappa = kappa  # This is the shape of the bonding curve
        self.days_to_80p_of_max_voting_weight = days_to_80p_of_max_voting_weight

        # Proposal may only request up to 20% of the funding pool
        self.max_proposal_request = max_proposal_request

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, attrs(self))

    def alpha(self) -> float:
        """
        Converts days_to_80p_of_max_voting_weight to alpha.
        alpha = 0.8 ^ (1/t)
        """
        return 0.8 ** (1/self.days_to_80p_of_max_voting_weight)

def bootstrap_simulation(c: CommonsSimulationConfiguration):
    contributions = [np.random.rand() * 10e5 for i in range(c.hatchers)]
    token_batches, initial_token_supply = create_token_batches(
        contributions, 0.1, c.vesting_80p_unlocked)

    commons = Commons(sum(contributions), initial_token_supply,
                      hatch_tribute=c.hatch_tribute, exit_tribute=c.exit_tribute, kappa=c.kappa)
    network = bootstrap_network(
        token_batches, c.proposals, commons._funding_pool, commons._token_supply, c.max_proposal_request)

    initial_conditions = {
        "network": network,
        "commons": commons,
        "funding_pool": commons._funding_pool,
        "collateral_pool": commons._collateral_pool,
        "token_supply": commons._token_supply,
        "policy_output": None,
        "sentiment": 0.5
    }

    # TODO: make it explicit that 1 timestep is 1 day
    simulation_parameters = {
        'T': range(30),
        'N': 1,
        'M': {
            # "sentiment_decay": 0.01, #termed mu in the state update function
            # "min_proposal_age_days": 7, # minimum periods passed before a proposal can pass,
            # "sentiment_sensitivity": 0.75,
            # 'min_supp':50, #number of tokens that must be stake for a proposal to be a candidate
            "debug": True,
            "alpha_days_to_80p_of_max_voting_weight": c.alpha(),
            "max_proposal_request": c.max_proposal_request,
        }
    }

    return initial_conditions, simulation_parameters


partial_state_update_blocks = [
    {
        "policies": {
            "generate_new_participants": GenerateNewParticipant.p_randomly,
        },
        'variables': {
            'network': GenerateNewParticipant.su_add_to_network,
            'commons': GenerateNewParticipant.su_add_investment_to_commons,
        }
    },
    sync_state_variables,
    {
        "policies": {
            "generate_new_proposals": GenerateNewProposal.p_randomly,
        },
        "variables": {
            "network": GenerateNewProposal.su_add_to_network,
        }
    },
    {
        "policies": {
            "generate_new_funding": GenerateNewFunding.p_exit_tribute_of_average_speculator_position_size,
        },
        "variables": {
            "network": GenerateNewFunding.su_add_funding,
        }
    },
    {
        "policies": {},
        "variables": {
            "network": ProposalFunding.su_update_age_and_conviction_thresholds,
        }
    },
    {
        "policies": {
            "which_proposals_should_be_funded": ProposalFunding.p_compare_conviction_and_threshold
        },
        "variables": {
            "network": ProposalFunding.su_make_proposal_active,
            "commons": ProposalFunding.su_deduct_funds_from_funding_pool,
            "policy_output": save_policy_output,
        }
    },
    {
        "policies": {},
        "variables": {
            "network": ParticipantExits.su_update_sentiment_when_proposal_becomes_active,
        }
    },
    sync_state_variables,
    {
        "policies": {
            "participants_stake_tokens_on_proposals": ParticipantVoting.p_participant_votes_on_proposal_according_to_affinity
        },
        "variables": {
            "network": ParticipantVoting.su_update_participants_votes,
        },
    },
    {
        "policies": {},
        "variables": {
            "network": ProposalFunding.su_calculate_conviction,
        }
    },
    {
        "policies": {
            "participants_decide_to_buy_tokens": ParticipantBuysTokens.p_decide_to_buy_tokens_bulk,
        },
        "variables": {
            "commons": ParticipantBuysTokens.su_buy_participants_tokens,
            "network": ParticipantBuysTokens.su_update_participants_tokens,
        }
    },
    sync_state_variables,
    {
        "policies": {
            "participants_decide_to_sell_tokens": ParticipantSellsTokens.p_decide_to_sell_tokens_bulk,
        },
        "variables": {
            "commons": ParticipantSellsTokens.su_burn_participants_tokens,
            "network": ParticipantSellsTokens.su_update_participants_tokens,
        }
    },
    {
        "policies": {
            "participants_may_exit": ParticipantExits.p_participant_decides_if_he_wants_to_exit,
        },
        "variables": {
            "commons": ParticipantExits.su_burn_exiters_tokens,
            "network": ParticipantExits.su_remove_participants_from_network,
        }
    },
    sync_state_variables
]
