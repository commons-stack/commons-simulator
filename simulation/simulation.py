from hatch import create_token_batches, TokenBatch, Commons

from entities import attrs
from policies import GenerateNewParticipant, GenerateNewProposal, GenerateNewFunding, ActiveProposals, ProposalFunding, ParticipantVoting
from network_utils import *


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


class CommonsSimulationConfiguration:
    """
    There are just so many options that passing them via kwargs has become
    rather unwieldy. Also it would be useful to have some footnotes next to each
    parameter.
    """

    def __init__(self):
        self.hatchers = 5
        self.proposals = 2
        self.hatch_tribute = 0.2
        self.vesting_80p_unlocked = 60  # 60 is 2 months until 80% of tokens are unlocked
        self.exit_tribute = 0.35
        self.kappa = 2  # This is the shape of the bonding curve
        self.days_to_80p_of_max_voting_weight = 10

        # Proposal may only request up to 20% of the funding pool
        self.max_proposal_request = 0.2

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, attrs(self))


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
            "days_to_80p_of_max_voting_weight": c.days_to_80p_of_max_voting_weight,
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
    {
        "policies": {},
        "variables": {
            "funding_pool": update_funding_pool,
            "collateral_pool": update_collateral_pool,
            "token_supply": update_token_supply,
        }
    },
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
            "decide_which_proposals_should_be_funded": ProposalFunding.p_compare_conviction_and_threshold
        },
        "variables": {
            "network": ProposalFunding.su_compare_conviction_and_threshold_make_proposal_active,
            "commons": ProposalFunding.su_compare_conviction_and_threshold_deduct_funds_from_funding_pool,
        }
    },
    {
        "policies": {},
        "variables": {
            "funding_pool": update_funding_pool,
            "collateral_pool": update_collateral_pool,
            "token_supply": update_token_supply,
        }
    },
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
]
