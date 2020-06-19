from scipy.stats import expon, gamma
import numpy as np
import networkx as nx
from hatch import TokenBatch
from convictionvoting import trigger_threshold
from IPython.core.debugger import set_trace
from functools import wraps
import pprint as pp
from entities import Participant, Proposal


def dump_output(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        result = f(*args, **kwargs)
        print("========== OUTPUT {} ==========".format(f.__name__))
        print(result)
        print("========== /OUTPUT ==========")
        return result
    return wrapper


def dump_input(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        print("========== INPUT {} ==========".format(f.__name__))
        print(*args, **kwargs)
        print("========== /INPUT ==========")
        result = f(*args, **kwargs)
        return result
    return wrapper


def get_nodes_by_type(g, node_type_selection):
    return [node for node in g.nodes if g.nodes[node]['type'] == node_type_selection]


def get_edges_by_type(g, edge_type_selection):
    return [edge for edge in g.edges if g.edges[edge]['type'] == edge_type_selection]


def get_proposals(network):
    return [i for i in network.nodes if isinstance(network.nodes[i]["item"], Proposal)]


def get_participants(network):
    return [i for i in network.nodes if isinstance(network.nodes[i]["item"], Participant)]


def initial_social_network(network: nx.DiGraph, scale=1, sigmas=3) -> nx.DiGraph:
    participants = get_participants(network)

    for i in participants:
        for j in participants:
            if not(j == i):
                influence_rv = expon.rvs(loc=0.0, scale=scale)
                if influence_rv > scale+sigmas*scale**2:
                    network.add_edge(i, j)
                    network.edges[(i, j)]['influence'] = influence_rv
                    network.edges[(i, j)]['type'] = 'influence'
    return network


def initial_conflict_network(network: nx.DiGraph, rate=.25) -> nx.DiGraph:
    proposals = get_proposals(network)

    for i in proposals:
        for j in proposals:
            if not(j == i):
                conflict_rv = np.random.rand()
                if conflict_rv < rate:
                    network.add_edge(i, j)
                    network.edges[(i, j)]['conflict'] = 1-conflict_rv
                    network.edges[(i, j)]['type'] = 'conflict'
    return network


def add_proposals_and_relationships_to_network(n: nx.DiGraph, proposals: int, funding_pool: float, token_supply: float) -> nx.DiGraph:
    participant_count = len(n)
    for i in range(proposals):
        j = participant_count + i
        n.add_node(j, type="proposal", conviction=0,
                   status="candidate", age=0)

        r_rv = gamma.rvs(3, loc=0.001, scale=10000)
        n.nodes[j]['funds_requested'] = r_rv
        n.nodes[j]['trigger'] = trigger_threshold(
            r_rv, funding_pool, token_supply)

        for i in range(participant_count):
            n.add_edge(i, j)
            rv = np.random.rand()
            a_rv = 1-4*(1-rv)*rv  # polarized distribution
            n.edges[(i, j)]['affinity'] = a_rv
            n.edges[(i, j)]['tokens'] = 0
            n.edges[(i, j)]['conviction'] = 0
            n.edges[(i, j)]['type'] = 'support'

        n = initial_conflict_network(n, rate=.25)
        n = initial_social_network(n, scale=1)
    return n


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
# =========================================================================================================


def gen_new_participant(network, new_participant_tokens):
    i = len([node for node in network.nodes])

    network.add_node(i)
    network.nodes[i]['type'] = "participant"

    s_rv = np.random.rand()
    network.nodes[i]['sentiment'] = s_rv
    network.nodes[i]['holdings_vesting'] = None
    network.nodes[i]['holdings_nonvesting'] = TokenBatch(
        new_participant_tokens)

    # Connect this new participant to existing proposals.
    for j in get_nodes_by_type(network, 'proposal'):
        network.add_edge(i, j)

        rv = np.random.rand()
        a_rv = 1-4*(1-rv)*rv  # polarized distribution
        network.edges[(i, j)]['affinity'] = a_rv
        network.edges[(i, j)]['tokens'] = a_rv * \
            network.nodes[i]['holdings_nonvesting'].value
        network.edges[(i, j)]['conviction'] = 0
        network.edges[(i, j)]['type'] = 'support'

    return network


def gen_new_proposal(network, funds, supply, trigger_func, scale_factor=1.0/100):
    j = len([node for node in network.nodes])
    network.add_node(j)
    network.nodes[j]['type'] = "proposal"

    network.nodes[j]['conviction'] = 0
    network.nodes[j]['status'] = 'candidate'
    network.nodes[j]['age'] = 0

    rescale = funds*scale_factor
    r_rv = gamma.rvs(3, loc=0.001, scale=rescale)
    network.nodes[j]['funds_requested'] = r_rv

    network.nodes[j]['trigger'] = trigger_func(r_rv, funds, supply)

    participants = get_nodes_by_type(network, 'participant')
    proposing_participant = np.random.choice(participants)

    for i in participants:
        network.add_edge(i, j)
        if i == proposing_participant:
            network.edges[(i, j)]['affinity'] = 1
        else:
            rv = np.random.rand()
            a_rv = 1-4*(1-rv)*rv  # polarized distribution
            network.edges[(i, j)]['affinity'] = a_rv

        network.edges[(i, j)]['conviction'] = 0
        network.edges[(i, j)]['tokens'] = 0
        network.edges[(i, j)]['type'] = 'support'

    return network


def calc_total_funds_requested(network):
    proposals = get_proposals(network)
    fund_requests = [network.nodes[j]['funds_requested']
                     for j in proposals if network.nodes[j]['status'] == 'candidate']
    total_funds_requested = np.sum(fund_requests)
    return total_funds_requested


def calc_median_affinity(network):
    supporters = get_edges_by_type(network, 'support')
    affinities = [network.edges[e]['affinity'] for e in supporters]
    median_affinity = np.median(affinities)
    return median_affinity


def gen_new_participants_proposals_funding_randomly(params, step, sL, s):
    network = s['network']
    commons = s['commons']
    funds = s['funding_pool']
    sentiment = s['sentiment']

    def randomly_gen_new_participant(participant_count, sentiment, current_token_supply, commons):
        arrival_rate = 10/(1+sentiment)
        rv1 = np.random.rand()
        new_participant = bool(rv1 < 1/arrival_rate)

        if new_participant:
            # Below line is quite different from Zargham's original, which gave
            # tokens instead. Here we randomly generate each participant's
            # post-Hatch investment, in DAI/USD. Here the settings for
            # expon.rvs() should generate investments of ~0-500 DAI.
            new_participant_investment = expon.rvs(loc=0.0, scale=100)
            new_participant_tokens = commons.dai_to_tokens(
                new_participant_investment)
            return new_participant, new_participant_investment, new_participant_tokens
        else:
            return new_participant, 0, 0

    def randomly_gen_new_proposal(total_funds_requested, median_affinity, funding_pool):
        proposal_rate = 1/median_affinity * \
            (1+total_funds_requested/funding_pool)
        rv2 = np.random.rand()
        new_proposal = bool(rv2 < 1/proposal_rate)
        return new_proposal

    def randomly_gen_new_funding(funds, sentiment):
        """
        Each step, more funding comes to the Commons through the exit tribute,
        because after the hatching phase, all incoming money goes to the
        collateral reserve, not to the funding pool.
        """
        scale_factor = funds*sentiment**2/10000
        if scale_factor < 1:
            scale_factor = 1

        # this shouldn't happen but expon is throwing domain errors
        if sentiment > .4:
            funds_arrival = expon.rvs(loc=0, scale=scale_factor)
        else:
            funds_arrival = 0
        return funds_arrival

    new_participant, new_participant_investment, new_participant_tokens = randomly_gen_new_participant(
        len(get_participants(network)), sentiment, s['token_supply'], commons)

    new_proposal = randomly_gen_new_proposal(
        calc_total_funds_requested(network), calc_median_affinity(network), funds)

    funds_arrival = randomly_gen_new_funding(funds, sentiment)

    return({'new_participant': new_participant,
            'new_participant_investment': new_participant_investment,
            'new_participant_tokens': new_participant_tokens,
            'new_proposal': new_proposal,
            'funds_arrival': funds_arrival})


def add_participants_proposals_to_network(params, step, sL, s, _input):
    network = s['network']
    funds = s['funding_pool']
    supply = s['token_supply']

    trigger_func = params[0]["trigger_threshold"]

    new_participant = _input['new_participant']  # T/F
    new_proposal = _input['new_proposal']  # T/F

    if new_participant:
        network = gen_new_participant(
            network, _input['new_participant_tokens'])

    if new_proposal:
        network = gen_new_proposal(network, funds, supply, trigger_func)

    # update age of the existing proposals
    proposals = get_nodes_by_type(network, 'proposal')

    for j in proposals:
        network.nodes[j]['age'] = network.nodes[j]['age']+1
        if network.nodes[j]['status'] == 'candidate':
            requested = network.nodes[j]['funds_requested']
            network.nodes[j]['trigger'] = trigger_func(
                requested, funds, supply)
        else:
            network.nodes[j]['trigger'] = np.nan

    key = 'network'
    value = network

    return (key, value)


def new_participants_and_new_funds_commons(params, step, sL, s, _input):
    commons = s["commons"]
    if _input['new_participant']:
        tokens, realized_price = commons.deposit(
            _input['new_participant_investment'])
        # print(tokens, realized_price, _input['new_participant_tokens'])
    if _input['funds_arrival']:
        commons._funding_pool += _input['funds_arrival']
    return "commons", commons
# =========================================================================================================


def make_active_proposals_complete_or_fail_randomly(params, step, sL, s):
    network = s['network']
    proposals = get_proposals(network)

    completed = []
    failed = []
    for j in proposals:
        if network.nodes[j]['status'] == 'active':
            grant_size = network.nodes[j]['funds_requested']
            base_completion_rate = params[0]['base_completion_rate']
            likelihood = 1.0/(base_completion_rate+np.log(grant_size))

            base_failure_rate = params[0]['base_failure_rate']
            failure_rate = 1.0/(base_failure_rate+np.log(grant_size))
            if np.random.rand() < likelihood:
                completed.append(j)
            elif np.random.rand() < failure_rate:
                failed.append(j)
    return({'completed': completed, 'failed': failed})


def get_sentimental(sentiment, force, decay=0):
    mu = decay
    sentiment = sentiment*(1-mu) + force
    if sentiment > 1:
        sentiment = 1
    return sentiment


def sentiment_decays_wo_completed_proposals(params, step, sL, s, _input):
    network = s['network']
    proposals = get_proposals(network)
    completed = _input['completed']
    failed = _input['failed']

    grants_outstanding = np.sum([network.nodes[j]['funds_requested']
                                 for j in proposals if network.nodes[j]['status'] == 'active'])
    grants_completed = np.sum(
        [network.nodes[j]['funds_requested'] for j in completed])
    grants_failed = np.sum(
        [network.nodes[j]['funds_requested'] for j in failed])

    sentiment = s['sentiment']

    if grants_outstanding > 0:
        force = (grants_completed-grants_failed)/grants_outstanding
    else:
        force = 1

    mu = params[0]['sentiment_decay']
    if (force >= 0) and (force <= 1):
        sentiment = get_sentimental(sentiment, force, mu)
    else:
        sentiment = get_sentimental(sentiment, 0, mu)

    key = 'sentiment'
    value = sentiment

    return (key, value)


def update_network_w_proposal_status(params, step, sL, s, _input):
    network = s['network']
    participants = get_participants(network)
    proposals = get_proposals(network)
    competitors = get_edges_by_type(network, 'conflict')
    completed = _input['completed']
    for j in completed:
        network.nodes[j]['status'] = 'completed'

        for c in proposals:
            if (j, c) in competitors:
                conflict = network.edges[(j, c)]['conflict']
                for i in participants:
                    network.edges[(i, c)]['affinity'] = network.edges[(
                        i, c)]['affinity'] * (1-conflict)

        for i in participants:
            force = network.edges[(i, j)]['affinity']
            sentiment = network.nodes[i]['sentiment']
            network.nodes[i]['sentiment'] = get_sentimental(
                sentiment, force, decay=0)

    failed = _input['failed']
    for j in failed:
        network.nodes[j]['status'] = 'failed'
        for i in participants:
            force = -network.edges[(i, j)]['affinity']
            sentiment = network.nodes[i]['sentiment']
            network.nodes[i]['sentiment'] = get_sentimental(
                sentiment, force, decay=0)

    key = 'network'
    value = network
    return (key, value)

# =========================================================================================================


def calculate_conviction(params, step, sL, s):
    def sort_proposals_by_conviction(network, proposals):
        ordered = sorted(
            proposals, key=lambda j: network.nodes[j]['conviction'], reverse=True)
        return ordered
    network = s['network']
    funding_pool = s['funding_pool']
    token_supply = s['token_supply']
    proposals = get_proposals(network)
    min_proposal_age = params[0]['min_proposal_age_days']
    trigger_func = params[0]['trigger_threshold']

    accepted = []
    triggers = {}
    funds_to_be_released = 0
    for j in proposals:
        if network.nodes[j]['status'] == 'candidate':
            requested = network.nodes[j]['funds_requested']
            age = network.nodes[j]['age']

            threshold = trigger_func(requested, funding_pool, token_supply)
            if age > min_proposal_age:
                conviction = network.nodes[j]['conviction']
                if conviction > threshold:
                    accepted.append(j)
                    funds_to_be_released = funds_to_be_released + requested
        else:
            threshold = np.nan

        triggers[j] = threshold

        # catch over release and keep the highest conviction results
        if funds_to_be_released > funding_pool:
            # print('funds ='+str(funds))
            # print(accepted)
            ordered = sort_proposals_by_conviction(network, accepted)
            # print(ordered)
            accepted = []
            release = 0
            ind = 0
            while release + network.nodes[ordered[ind]]['funds_requested'] < funding_pool:
                accepted.append(ordered[ind])
                release = network.nodes[ordered[ind]]['funds_requested']
                ind = ind+1

    return({'accepted': accepted, 'triggers': triggers})


def decrement_commons_funding_pool(params, step, sL, s, _input):
    commons = s['commons']
    network = s['network']
    accepted = _input['accepted']

    for j in accepted:
        commons.spend(network.nodes[j]['funds_requested'])

    key = 'commons'
    value = commons
    return (key, value)


def update_sentiment_on_release(params, step, sL, s, _input):
    network = s['network']
    proposals = get_proposals(network)
    accepted = _input['accepted']

    proposals_outstanding = np.sum([network.nodes[j]['funds_requested']
                                    for j in proposals if network.nodes[j]['status'] == 'candidate'])
    proposals_accepted = np.sum(
        [network.nodes[j]['funds_requested'] for j in accepted])

    sentiment = s['sentiment']
    force = proposals_accepted/proposals_outstanding
    if (force >= 0) and (force <= 1):
        sentiment = get_sentimental(sentiment, force, False)
    else:
        sentiment = get_sentimental(sentiment, 0, False)

    key = 'sentiment'
    value = sentiment
    return (key, value)


def update_proposals(params, step, sL, s, _input):
    network = s['network']
    accepted = _input['accepted']
    triggers = _input['triggers']
    participants = get_participants(network)
    proposals = get_proposals(network)
    sentiment_sensitivity = params[0]['sentiment_sensitivity']

    # Update candidate proposals with their new conviction thresholds (if any)
    for j in proposals:
        network.nodes[j]['trigger'] = triggers[j]

    # bookkeeping conviction and participant sentiment
    for j in accepted:
        network.nodes[j]['status'] = 'active'
        network.nodes[j]['conviction'] = np.nan
        # change status to active
        for i in participants:
            # operating on edge = (i,j)
            # reset tokens assigned to other candidates
            network.edges[(i, j)]['tokens'] = 0
            network.edges[(i, j)]['conviction'] = np.nan

            # update participants sentiments (positive or negative)
            affinities = [network.edges[(i, p)]['affinity']
                          for p in proposals if not(p in accepted)]
            if len(affinities) > 1:
                max_affinity = np.max(affinities)
                force = network.edges[(i, j)]['affinity'] - \
                    sentiment_sensitivity*max_affinity
            else:
                force = 0

            # based on what their affinities to the accepted proposals
            network.nodes[i]['sentiment'] = get_sentimental(
                network.nodes[i]['sentiment'], force, False)

    key = 'network'
    value = network
    return (key, value)
# =========================================================================================================


def participants_buy_more_if_they_feel_good_and_vote_for_proposals(params, step, sL, s):
    network = s['network']
    participants = get_participants(network)
    proposals = get_proposals(network)
    candidate_proposals = [
        j for j in proposals if network.nodes[j]['status'] == 'candidate']
    sentiment_sensitivity = params[0]['sentiment_sensitivity']

    delta_holdings = {}
    proposals_supported = {}
    for i in participants:
        engagement_rate = .3*network.nodes[i]['sentiment']
        if np.random.rand() < engagement_rate:
            force = network.nodes[i]['sentiment']-sentiment_sensitivity
            # because implementing "vesting+nonvesting holdings" calculation is best done outside the scope of this function
            delta_holdings[i] = np.random.rand()*force

            support = []
            for j in candidate_proposals:
                affinity = network.edges[(i, j)]['affinity']
                cutoff = sentiment_sensitivity * \
                    np.max([network.edges[(i, p)]['affinity']
                            for p in candidate_proposals])
                if cutoff < .5:
                    cutoff = .5

                if affinity > cutoff:
                    support.append(j)

            proposals_supported[i] = support
        else:
            delta_holdings[i] = 0
            proposals_supported[i] = [
                j for j in candidate_proposals if network.edges[(i, j)]['tokens'] > 0]

    return({'delta_holdings': delta_holdings, 'proposals_supported': proposals_supported})


def update_holdings_nonvesting_of_participants(params, step, sL, s, _input):
    network = s['network']
    proposals = get_proposals(network)
    proposals_supported = _input['proposals_supported']
    alpha = params[0]['alpha']
    candidates = [j for j in proposals if network.nodes[j]
                  ['status'] == 'candidate']
    min_support = params[0]['min_supp']

    # Update the participants holdings
    participants = get_participants(network)
    for i in participants:
        network.nodes[i]["holdings_nonvesting"].value += _input["delta_holdings"][i]
        supported = proposals_supported[i]
        total_affinity = np.sum(
            [network.edges[(i, j)]['affinity'] for j in supported])
        for j in candidates:
            if j in supported:
                normalized_affinity = network.edges[(
                    i, j)]['affinity']/total_affinity
                network.edges[(i, j)]['tokens'] = normalized_affinity * \
                    network.nodes[i]['holdings_nonvesting'].value
            else:
                network.edges[(i, j)]['tokens'] = 0

            prior_conviction = network.edges[(i, j)]['conviction']
            current_tokens = network.edges[(i, j)]['tokens']
            network.edges[(i, j)]['conviction'] = current_tokens + \
                alpha*prior_conviction

    for j in candidates:
        network.nodes[j]['conviction'] = np.sum(
            [network.edges[(i, j)]['conviction'] for i in participants])
        total_tokens = np.sum([network.edges[(i, j)]['tokens']
                               for i in participants])
        if total_tokens < min_support:
            network.nodes[j]['status'] = 'killed'
    return ("network", network)
