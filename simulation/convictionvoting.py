import numpy as np
import config


def trigger_threshold(funds_requested, funding_pool, token_supply, max_proposal_request):
    """
    funds_requested: funds requested by the proposal
    funding_pool: the current size of the funding pool
    token_supply: current token_supply
    max_proposal_request: maximum fraction of the funding pool that a proposal can ever request
    """
    rho = config.rho_multiplier * max_proposal_request**config.rho_power

    fraction = funds_requested/funding_pool
    if fraction < max_proposal_request:
        return rho*token_supply/(max_proposal_request-fraction)**2
    else:
        return np.inf
