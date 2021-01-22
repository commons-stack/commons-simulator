from typing import Tuple
import numpy as np
import copy
from hatch import (create_token_batches, Commons,
                   convert_80p_to_cliff_and_halflife)

from entities import attrs
from policies import (GenerateNewParticipant, GenerateNewProposal,
                      GenerateNewFunding, ActiveProposals, ProposalFunding,
                      ParticipantVoting, ParticipantSellsTokens,
                      ParticipantBuysTokens, ParticipantExits,
                      ParticipantSentiment)
from network_utils import bootstrap_network, calc_avg_sentiment
from utils import (new_probability_func, new_exponential_func, new_gamma_func,
                   new_random_number_func, new_choice_func)


def update_collateral_pool(params, step, sL, s, _input):
    commons = s["commons"]
    s["collateral_pool"] = commons._collateral_pool
    return "collateral_pool", commons._collateral_pool


def update_token_supply(params, step, sL, s, _input):
    commons = s["commons"]
    s["token_supply"] = commons._token_supply
    return "token_supply", commons._token_supply


def update_token_price(params, step, sL, s, _input):
    commons = s["commons"]
    s["token_price"] = commons.token_price()
    return "token_price", commons.token_price()


def update_funding_pool(params, step, sL, s, _input):
    commons = s["commons"]
    s["funding_pool"] = commons._funding_pool
    return "funding_pool", commons._funding_pool


def update_avg_sentiment(params, step, sL, s, _input):
    network = s["network"]
    s = calc_avg_sentiment(network)
    return "sentiment", s

def network_deepcopy(params, step, sL, s, _input):
    network = s["network"]
    return "network", copy.deepcopy(network)


def save_policy_output(params, step, sL, s, _input):
    return "policy_output", _input


# This sub-policy block should be run every time the Commons object is updated.
sync_state_variables = {
    "label": "Sync state variables",
    "policies": {},
    "variables": {
        "funding_pool": update_funding_pool,
        "collateral_pool": update_collateral_pool,
        "token_supply": update_token_supply,
        "token_price": update_token_price,
        "sentiment": update_avg_sentiment,
    }
}

network_snapshot = {
    "label": "Get a snapshop of the network",
    "policies": {},
    "variables": {
        "network": network_deepcopy,
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
                 vesting_80p_unlocked=120,
                 exit_tribute=0.35,
                 kappa=2,
                 days_to_80p_of_max_voting_weight=10,
                 max_proposal_request=0.2,
                 timesteps_days=730,
                 random_seed=None):
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

        self.timesteps_days = timesteps_days  # Simulate 2*365=730 days

        self.random_seed = random_seed
        self.probability_func = new_probability_func(random_seed)
        self.exponential_func = new_exponential_func(random_seed)
        self.gamma_func = new_gamma_func(random_seed)
        self.random_number_func = new_random_number_func(random_seed)
        self.choice_func = new_choice_func(random_seed)

        self.speculation_days = int(.2 * vesting_80p_unlocked) + int(0.6 * vesting_80p_unlocked * self.random_number_func())
        self.multiplier_new_participants = 1 + int(9 * self.random_number_func())

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, attrs(self))

    def alpha(self) -> float:
        """
        Converts days_to_80p_of_max_voting_weight to alpha.
        alpha = (1 - 0.8) ^ (1/t)
        """
        return 0.2 ** (1/self.days_to_80p_of_max_voting_weight)

    def cliff_and_halflife(self) -> Tuple[float, float]:
        """
        This is just a wrapper around hatch.convert_80p_to_cliff_and_halflife().
        It is used here instead for logical consistency (having all derived
        configuration variables come from CommonsSimulationConfiguration), but
        defined in hatch for local consistency (having all hatch-related code in
        one place). Time will tell if this really matters.
        """
        return convert_80p_to_cliff_and_halflife(self.vesting_80p_unlocked)


def bootstrap_simulation(c: CommonsSimulationConfiguration):
    contributions = [c.random_number_func() * 10e5 for i in range(c.hatchers)]
    cliff_days, halflife_days = c.cliff_and_halflife()
    token_batches, initial_token_supply = create_token_batches(
        contributions, 0.1, cliff_days, halflife_days)

    commons = Commons(sum(contributions), initial_token_supply,
                      hatch_tribute=c.hatch_tribute, exit_tribute=c.exit_tribute, kappa=c.kappa)
    network = bootstrap_network(
        token_batches, c.proposals, commons._funding_pool, commons._token_supply, c.max_proposal_request,
        c.probability_func, c.random_number_func, c.gamma_func, c.exponential_func)

    initial_conditions = {
        "network": network,
        "commons": commons,
        "funding_pool": commons._funding_pool,
        "collateral_pool": commons._collateral_pool,
        "token_supply": commons._token_supply,
        "token_price": commons.token_price(),
        "policy_output": None,
        "sentiment": 0.75
    }

    simulation_parameters = {
        'T': range(c.timesteps_days),
        'N': 1,
        'M': {
            # "sentiment_decay": 0.01, #termed mu in the state update function
            # "min_proposal_age_days": 7, # minimum periods passed before a proposal can pass,
            # "sentiment_sensitivity": 0.75,
            # 'min_supp':50, #number of tokens that must be stake for a proposal to be a candidate
            "debug": False,
            "alpha_days_to_80p_of_max_voting_weight": c.alpha(),
            "max_proposal_request": c.max_proposal_request,
            "random_seed": c.random_seed,
            "probability_func": c.probability_func,
            "exponential_func": c.exponential_func,
            "gamma_func": c.gamma_func,
            "random_number_func": c.random_number_func,
            "choice_func": c.choice_func,
            "speculation_days": c.speculation_days,
            "multiplier_new_participants": c.multiplier_new_participants
        }
    }

    return initial_conditions, simulation_parameters


partial_state_update_blocks = [
    {
        "label": "Generate new participants",
        "policies": {
            "generate_new_participants": GenerateNewParticipant.p_randomly,
        },
        'variables': {
            'network': GenerateNewParticipant.su_add_to_network,
            'commons': GenerateNewParticipant.su_add_investment_to_commons,
        }
    },
    {
        "label": "Update participants' token batch age",
        "policies": {},
        "variables": {
            "network": GenerateNewParticipant.su_update_participants_token_batch_age,
        }
    },
    sync_state_variables,
    {
        "label": "Generate new proposals",
        "policies": {
            "generate_new_proposals": GenerateNewProposal.p_randomly,
        },
        "variables": {
            "network": GenerateNewProposal.su_add_to_network,
        }
    },
    {
        "label": "Generate new funding",
        "policies": {
            "generate_new_funding": GenerateNewFunding.p_exit_tribute_of_average_speculator_position_size,  # TODO: Doesn't interact with the BC
        },
        "variables": {
            "network": GenerateNewFunding.su_add_funding,
        }
    },
    {
        "label": "Update proposals' age and conviction thresholds",
        "policies": {},
        "variables": {
            "network": ProposalFunding.su_update_age_and_conviction_thresholds,
        }
    },
    {
        "label": "Compare proposals' conviction and thresholds",
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
        "label": "Update participants' sentiment when a proposal becomes active",
        "policies": {},
        "variables": {
            "network": ParticipantExits.su_update_sentiment_when_proposal_becomes_active,
        }
    },
    sync_state_variables,
    {
        "label": "Proposals become failed or completed",
        "policies": {
            "which_proposals_are_failed_or_completed": ActiveProposals.p_influenced_by_grant_size
        },
        "variables": {
            "network": ActiveProposals.su_set_proposal_status,
            "policy_output": save_policy_output,
        }
    },
    {
        "label": "Update participants' sentiment when a proposal becomes failed or completed",
        "policies": {},
        "variables": {
            "network": ParticipantExits.su_update_sentiment_when_proposal_becomes_failed_or_completed,
        }
    },
    {
        "label": "Participant votes on proposal according to affinity",
        "policies": {
            "participants_stake_tokens_on_proposals": ParticipantVoting.p_participant_votes_on_proposal_according_to_affinity
        },
        "variables": {
            "network": ParticipantVoting.su_update_participants_votes,
        },
    },
    {
        "label": "Calculate proposals' conviction",
        "policies": {},
        "variables": {
            "network": ProposalFunding.su_calculate_conviction,
        }
    },
    {
        "label": "Participant decides to buy tokens",
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
        "label": "Participant decides to sell tokens",
        "policies": {
            "participants_decide_to_sell_tokens": ParticipantSellsTokens.p_decide_to_sell_tokens_bulk,
        },
        "variables": {
            "commons": ParticipantSellsTokens.su_burn_participants_tokens,
            "network": ParticipantSellsTokens.su_update_participants_tokens,
        }
    },
    {
        "label": "Participant decides if he wants to exit",
        "policies": {
            "participants_may_exit": ParticipantExits.p_participant_decides_if_he_wants_to_exit,
        },
        "variables": {
            "commons": ParticipantExits.su_burn_exiters_tokens,
            "network": ParticipantExits.su_remove_participants_from_network,
        }
    },
    {
        "label": "Participants' sentiment decays",
        "policies": {},
        "variables": {
            "network": ParticipantSentiment.su_update_sentiment_decay,
        }
    },
    sync_state_variables,
    # network_snapshot,  # Enable it only if running an A/B testing or parameter sweep with a no_deepcopy version of cadCAD
]
