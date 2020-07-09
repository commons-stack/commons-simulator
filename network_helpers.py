from scipy.stats import expon, gamma
import numpy as np
import networkx as nx
from hatch import TokenBatch
from convictionvoting import trigger_threshold
from IPython.core.debugger import set_trace
from functools import wraps
import pprint as pp
from entities import Participant, Proposal, ProposalStatus


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


def get_edges_by_type(g, edge_type_selection):
    return [edge for edge in g.edges if g.edges[edge]['type'] == edge_type_selection]


def get_proposals(network, status: ProposalStatus = None):
    proposals = [i for i in network.nodes if isinstance(
        network.nodes[i]["item"], Proposal)]
    if status:
        return [j for j in proposals if network.nodes[j]['item'].status == status]
    return proposals


def get_participants(network):
    return [i for i in network.nodes if isinstance(network.nodes[i]["item"], Participant)]


def initial_social_network(network: nx.DiGraph, scale=1, sigmas=3) -> nx.DiGraph:
    """
    Calculates the chances that a Participant is influential enough to have an
    'influence' edge in the network to other Participants, and sets it up.
    """
    participants = get_participants(network)

    for i in participants:
        for j in participants:
            if not(j == i):
                # This exponential distribution gives you a lot more values
                # smaller than 1, but quite a few outliers that could go all the
                # way up to even 8.
                influence_rv = expon.rvs(loc=0.0, scale=scale)
                # Unless your influence is 3 standard deviations above the norm
                # (where scale determines the size of the standard deviation),
                # you don't have any influence at all.
                if influence_rv > scale+sigmas*scale**2:
                    network.add_edge(i, j)
                    network.edges[(i, j)]['influence'] = influence_rv
                    network.edges[(i, j)]['type'] = 'influence'
    return network


def initial_conflict_network(network: nx.DiGraph, rate=.25) -> nx.DiGraph:
    """
    Supporting one Proposal may mean going against another Proposal, in which
    case a Proposal-Proposal conflict edge is created. This function calculates
    the chances of that happening and the 'strength' of such a conflict.
    """
    proposals = get_proposals(network)

    for i in proposals:
        for j in proposals:
            if not(j == i):
                # (rate=0.25) means 25% of other Proposals are going to conflict
                # with this particular Proposal. And when they do conflict, the
                # conflict number is high (at least 1 - 0.25 = 0.75).
                conflict_rv = np.random.rand()
                if conflict_rv < rate:
                    network.add_edge(i, j)
                    network.edges[(i, j)]['conflict'] = 1-conflict_rv
                    network.edges[(i, j)]['type'] = 'conflict'
    return network


def add_proposals_and_relationships_to_network(n: nx.DiGraph, proposals: int, funding_pool: float, token_supply: float) -> nx.DiGraph:
    """
    At this point, there are Participants in the network but they are not
    related to each other. This function adds Proposals as nodes and the
    relationships between every Participant and these new Proposals.
    """
    participant_count = len(n)
    for i in range(proposals):
        j = participant_count + i
        r_rv = gamma.rvs(3, loc=0.001, scale=10000)

        proposal = Proposal(funds_requested=r_rv, trigger=trigger_threshold(
            r_rv, funding_pool, token_supply))
        n.add_node(j, item=proposal)

        for i in range(participant_count):
            n.add_edge(i, j)
            rv = np.random.rand()
            a_rv = 1-4*(1-rv)*rv  # polarized distribution
            # Token Holder -> Proposal Relationship
            # Looks like Zargham skewed this distribution heavily towards
            # numbers smaller than 0.25 This is the affinity towards proposals.
            # Most Participants won't care about most proposals, but then there
            # will be a few Proposals that they really care about.
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


def print_proposal_status(params, step, sL, s, _input):
    network = s["network"]
    candidates = len(get_proposals(network, status=ProposalStatus.CANDIDATE))
    active = len(get_proposals(network, status=ProposalStatus.ACTIVE))
    completed = len(get_proposals(network, status=ProposalStatus.COMPLETED))
    failed = len(get_proposals(network, status=ProposalStatus.FAILED))
    print("Proposals: CANDIDATE {} ACTIVE {} COMPLETED {} FAILED {}".format(
        candidates, active, completed, failed))
    return "network", network

# =========================================================================================================


def gen_new_participant(network, new_participant_tokens):
    """
    Create a new Participant, and calculate his relationship to existing Proposals.
    """
    i = len([node for node in network.nodes])

    network.add_node(i)
    network.nodes[i]['item'] = Participant(
        holdings_vesting=None, holdings_nonvesting=TokenBatch(new_participant_tokens))

    for j in get_proposals(network):
        network.add_edge(i, j)

        rv = np.random.rand()
        a_rv = 1-4*(1-rv)*rv
        # Most Proposals he finds 'meh', but some Proposals he likes a lot. The
        # amount of tokens he invests in a Proposal is proportional to his
        # affinity for them.
        network.edges[(i, j)]['affinity'] = a_rv
        network.edges[(i, j)]['tokens'] = a_rv * \
            network.nodes[i]['item'].holdings_nonvesting.value
        network.edges[(i, j)]['conviction'] = 0
        network.edges[(i, j)]['type'] = 'support'

    return network


def gen_new_proposal(network, funds, supply, trigger_func, scale_factor=1.0/100):
    """
    Add a new Proposal to the network. Connect it with all Participants.

    If the Participant is the one who made this Proposal, his affinity for it is
    1. Otherwise, the affinity is calculated the same way as in gen_new_participant().
    """
    j = len([node for node in network.nodes])

    rescale = funds*scale_factor
    r_rv = gamma.rvs(3, loc=0.001, scale=rescale)
    proposal = Proposal(funds_requested=r_rv,
                        trigger=trigger_func(r_rv, funds, supply))
    network.add_node(j, item=proposal)

    participants = get_participants(network)
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
    candidates = get_proposals(network, status=ProposalStatus.CANDIDATE)
    fund_requests = [network.nodes[j]
                     ["item"].funds_requested for j in candidates]
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
    funding_pool = s['funding_pool']
    sentiment = s['sentiment']

    def randomly_gen_new_participant(participant_count, sentiment, current_token_supply, commons):
        """
        If the Commons sentiment is high (as given by calling function), then
        more Participants will be generated?

        Randomly generate the amount of collateral that the new Participant puts
        into the funding pool. Calcualte how many tokens he would get for that
        price, without actually updating Commons. That will be done by the state
        update functions.
        """
        # The sentiment can range from 0-1.0, therefore the rate at which new
        # Participants arrive can range from 10-20%.
        arrival_rate = (1+sentiment)/10
        new_participant = bool(np.random.rand() < arrival_rate)

        if new_participant:
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
            new_participant_investment = expon.rvs(loc=0.0, scale=100)
            new_participant_tokens = commons.dai_to_tokens(
                new_participant_investment)
            return new_participant, new_participant_investment, new_participant_tokens
        else:
            return new_participant, 0, 0

    def randomly_gen_new_proposal(total_funds_requested, median_affinity, funding_pool):
        """
        The intent of this equation is:

        If the median affinity is high, the Proposal Rate should be high.

        If total funds_requested in candidate proposals is much lower than the
        funding pool (i.e. the Commons has lots of spare money), then people are
        just going to pour in more Proposals.
        """
        percent_of_funding_pool_being_requested = total_funds_requested/funding_pool
        proposal_rate = median_affinity / \
            (1 + percent_of_funding_pool_being_requested)
        new_proposal = bool(np.random.rand() < proposal_rate)
        return new_proposal

    def randomly_gen_new_funding(funding_pool, sentiment):
        """
        Randomly generates the funding that comes to the Commons from
        speculators' trades. This implementation does not however take into
        account an exit tribute! Remember after the hatching phase, all incoming
        money goes to the collateral reserve, not to the funding pool.

        Dividing the funding pool by x (in this case 10000) means that if the
        funding pool is less than x, speculators won't trade in its token
        because they think "this Commons is dead or dying".
        """
        scale_factor = (funding_pool/10000) * sentiment**2
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
        calc_total_funds_requested(network), calc_median_affinity(network), funding_pool)

    funds_arrival = randomly_gen_new_funding(funding_pool, sentiment)

    return({'new_participant': new_participant,
            'new_participant_investment': new_participant_investment,
            'new_participant_tokens': new_participant_tokens,
            'new_proposal': new_proposal,
            'funds_arrival': funds_arrival})


def add_participants_proposals_to_network(params, step, sL, s, _input):
    """
    If the policy function has decided to generate a new participant, add one to
    the network. Same for the proposal.

    For each Proposal, update its age and update its conviction threshold (to pass).
    """
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

    # Update age of existing Proposals, and thus the trigger.
    proposals = get_proposals(network)

    for j in proposals:
        network.nodes[j]["item"].age = network.nodes[j]["item"].age+1
        if network.nodes[j]["item"].status == ProposalStatus.CANDIDATE:
            requested = network.nodes[j]["item"].funds_requested
            network.nodes[j]["item"].trigger = trigger_func(
                requested, funds, supply)
        else:
            network.nodes[j]["item"].trigger = np.nan

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
    """
    Whether a proposal completes or fails depends on its grant size. If it has a
    large grant size, it is harder for it to pass or fail, because huge things
    take time to move or get to a specific conclusion.

    BUG: base_completion_rate, base_failure_rate were never in params! we
    probably never hit this because proposals weren't becoming active.
    """
    network = s['network']
    active_proposals = get_proposals(network, status=ProposalStatus.ACTIVE)

    completed = []
    failed = []
    for j in active_proposals:
        grant_size = network.nodes[j]['item'].funds_requested

        base_completion_rate = params[0]['base_completion_rate']
        base_failure_rate = params[0]['base_failure_rate']
        # when base_completion_rate = 100, the completion rate will be 1%,
        # fudged a little bit by the grant size.
        likelihood = 1.0/(base_completion_rate+np.log(grant_size))
        # same thing for the failure rate, except now the failure rate is 0.5%.
        # Basically we are assuming that Proposals are half as likely to fail as
        # to succeed.
        failure_rate = 1.0/(base_failure_rate+np.log(grant_size))

        if np.random.rand() < likelihood:
            completed.append(j)
        elif np.random.rand() < failure_rate:
            failed.append(j)
    return({'completed': completed, 'failed': failed})


def get_sentimental(sentiment, force, decay=0):
    """
    Sentiment goes down by, say, 10% each timestep, (look at the decay variable)
    but is replenished by the force, which is added to the sentiment.
    """
    mu = decay
    sentiment = sentiment*(1-mu) + force
    if sentiment > 1:
        sentiment = 1
    return sentiment


def sentiment_decays_wo_completed_proposals(params, step, sL, s, _input):
    """
    The policy before has determined which active proposals are going to
    complete/fail. The assumption here seems to be that larger grants will
    affect sentiment more if they succeed/fail.

    force = grants_completed - grants_failed
            ________________________________
                    grants_outstanding

    This force pushes the sentiment up, but the max value of force can only be 1
    """
    def calculate_force(grants_completed, grants_failed, grants_outstanding):
        if grants_outstanding > 0:
            force = (grants_completed-grants_failed)/grants_outstanding
        else:
            force = 1
        return force

    network = s['network']
    active_proposals = get_proposals(network, status=ProposalStatus.ACTIVE)
    completed = _input['completed']
    failed = _input['failed']

    grants_outstanding = np.sum([network.nodes[j]['item'].funds_requested
                                 for j in active_proposals])
    grants_completed = np.sum(
        [network.nodes[j]['item'].funds_requested for j in completed])
    grants_failed = np.sum(
        [network.nodes[j]['item'].funds_requested for j in failed])

    sentiment = s['sentiment']
    mu = params[0]['sentiment_decay']
    force = calculate_force(
        grants_completed, grants_failed, grants_outstanding)
    if (force >= 0) and (force <= 1):
        sentiment = get_sentimental(sentiment, force, mu)
    else:
        sentiment = get_sentimental(sentiment, 0, mu)

    return 'sentiment', sentiment


def update_network_w_proposal_status(params, step, sL, s, _input):
    """
    Update the participant's affinity to each proposal.
    If the Proposal was completed, then the Participant gets a nice boost to his sentiment.
    If the Proposal failed, then the Participant's sentiment gets a negative force.

    TODO: For a completed Proposal, its competing Proposals will now have less affinity from all Participants?
    Participant's Affinity to a Proposal =       affinity
                                          _______________________
                                               1 - conflict
    """
    network = s['network']
    participants = get_participants(network)
    proposals = get_proposals(network)
    competitors = get_edges_by_type(network, 'conflict')
    completed = _input['completed']
    for j in completed:
        # When a Proposal completes, then there is less need for the other
        # Proposals that conflicted with it. Thus the Participants' affinities
        # to the competing Proposals would drop.
        #
        # TODO: Competing Proposals should also get a negative nudge when a
        # Proposal becomes ACTIVE.
        network.nodes[j]["item"].status = ProposalStatus.COMPLETED

        for c in proposals:
            if (j, c) in competitors:
                conflict = network.edges[(j, c)]['conflict']
                for i in participants:
                    network.edges[(i, c)]['affinity'] = network.edges[(
                        i, c)]['affinity'] * (1-conflict)

        for i in participants:
            force = network.edges[(i, j)]['affinity']
            sentiment = network.nodes[i]["item"].sentiment
            network.nodes[i]["item"].sentiment = get_sentimental(
                sentiment, force, decay=0)

    failed = _input['failed']
    for j in failed:
        network.nodes[j]["item"].status = ProposalStatus.FAILED
        for i in participants:
            force = -network.edges[(i, j)]['affinity']
            sentiment = network.nodes[i]["item"].sentiment
            network.nodes[i]["item"].sentiment = get_sentimental(
                sentiment, force, decay=0)

    key = 'network'
    value = network
    return (key, value)

# =========================================================================================================


def calculate_conviction(params, step, sL, s):
    """
    Look at all the candidate proposals.

    Calculate their new conviction thresholds (they change depending on the
    funding_pool and token_supply) - if the Proposal's conviction is above this
    threshold, it is accepted.

    Proposals need to be a minimum age before they can get accepted.

    But if accepting these new proposals would empty the funding pool,
    prioritize Proposals with the highest conviction.
    """
    def sort_proposals_by_conviction(network, proposals):
        ordered = sorted(
            proposals, key=lambda j: network.nodes[j]['item'].conviction, reverse=True)
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
        if network.nodes[j]['item'].status == ProposalStatus.CANDIDATE:
            requested = network.nodes[j]['item'].funds_requested
            age = network.nodes[j]['item'].age

            threshold = trigger_func(requested, funding_pool, token_supply)
            if age > min_proposal_age:
                conviction = network.nodes[j]['item'].conviction
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
            while release + network.nodes[ordered[ind]]['item'].funds_requested < funding_pool:
                accepted.append(ordered[ind])
                release = network.nodes[ordered[ind]]['item'].funds_requested
                ind = ind+1

    return({'accepted': accepted, 'triggers': triggers})


def decrement_commons_funding_pool(params, step, sL, s, _input):
    commons = s['commons']
    network = s['network']
    accepted = _input['accepted']

    for j in accepted:
        commons.spend(network.nodes[j]['item'].funds_requested)

    return 'commons', commons


def update_sentiment_on_funding_proposals(params, step, sL, s, _input):
    """
    When a Proposal becomes ACTIVE, this can only be a positive boost to the
    Commons' sentiment. The question is only how much.

    If the size (measured by funds allocated) of Active Proposals is larger than
    Proposals waiting to be funded, then there is a positive boost to the
    sentiment (force).

    By now it is obvious that there is no standard calculation of "force". It
    just has to be 0 < force < 1.
    """
    network = s['network']
    candidates = get_proposals(network, status=ProposalStatus.CANDIDATE)
    active = _input['accepted']

    proposals_candidate = np.sum([network.nodes[j]['item'].funds_requested
                                  for j in candidates])
    proposals_active = np.sum(
        [network.nodes[j]['item'].funds_requested for j in active])

    sentiment = s['sentiment']
    force = proposals_active/proposals_candidate
    if (force >= 0) and (force <= 1):
        sentiment = get_sentimental(sentiment, force, False)
    else:
        sentiment = get_sentimental(sentiment, 0, False)

    return 'sentiment', sentiment


def update_proposals(params, step, sL, s, _input):
    """
    Proposals: once they've been voted in, clear the conviction value and set
    their status to "Active". The tokens staked on this Proposal are set to 0
    and the conviction gathered by a Participant on a particular Proposal is
    also set to NaN.

    If the Participant has no relationship to any other Proposals, force is 0
    and his sentiment will not change (because the decay is set to 0)
    If he has relationships to other Proposals, take the largest affinity he has...
    force affecting Participant's sentiment =     affinity (to a particular
    Proposal) - sentiment_sensitivity * max_affinity
    """
    network = s['network']
    accepted = _input['accepted']
    triggers = _input['triggers']
    participants = get_participants(network)
    proposals = get_proposals(network)
    sentiment_sensitivity = params[0]['sentiment_sensitivity']

    # Update candidate proposals with their new conviction thresholds (if any)
    # BUG: How does this work with add_participants_proposals_to_network()
    # conviction threshold calculation?
    for j in proposals:
        network.nodes[j]['trigger'] = triggers[j]

    # bookkeeping conviction and participant sentiment
    for j in accepted:
        network.nodes[j]['item'].status = ProposalStatus.ACTIVE
        network.nodes[j]['item'].conviction = np.nan
        # change status to active
        for i in participants:
            # reset tokens assigned to other candidates
            network.edges[(i, j)]['tokens'] = 0
            network.edges[(i, j)]['conviction'] = np.nan

            # Let's look at Participants' relationships to other, non-accepted Proposals
            # BUG: does this include hitherto FAILED/COMPLETED/CANDIDATE Proposals?
            affinities = [network.edges[(i, p)]['affinity']
                          for p in proposals if not(p in accepted)]

            # The Participant's sentiment should change when a Proposal gets
            # accepted. Calculate the force at which the sentiment changes based
            # on his affinity.
            # BUG: what about Proposals that the Participant didn't like? No
            # mention of negative affinities so far... or is that elsewhere?
            if len(affinities) > 1:
                max_affinity = np.max(affinities)
                # force CAN be negative after all, if you realize that affinity
                # can be 0. But this is not expressed anywhere explicitly.
                force = network.edges[(i, j)]['affinity'] - \
                    sentiment_sensitivity*max_affinity
            else:
                force = 0

            # based on what their affinities to the accepted proposals
            network.nodes[i]['item'].sentiment = get_sentimental(
                network.nodes[i]['item'].sentiment, force, 0)

    key = 'network'
    value = network
    return (key, value)
# =========================================================================================================


def participants_buy_more_if_they_feel_good_and_vote_for_proposals(params, step, sL, s):
    """
    The higher a Participant's sentiment, the more he will interact with the Commons.

    TODO: don't quite understand how his affinity makes him interact with proposals and cutoff
    """

    network = s['network']
    participants = get_participants(network)
    candidate_proposals = get_proposals(
        network, status=ProposalStatus.CANDIDATE)
    sentiment_sensitivity = params[0]['sentiment_sensitivity']

    delta_holdings = {}
    proposals_supported = {}
    for i in participants:
        engagement_rate = .3*network.nodes[i]['item'].sentiment
        if np.random.rand() < engagement_rate:
            force = network.nodes[i]['item'].sentiment-sentiment_sensitivity
            # because implementing "vesting+nonvesting holdings" calculation is best done outside the scope of this function
            delta_holdings[i] = np.random.rand()*force

            # Put your tokens on your favourite Proposals, where favourite is
            # calculated as 0.75 * (the affinity for the Proposal you like the
            # most) e.g. if there are 2 Proposals that you have affinity 0.8,
            # 0.9, then 0.75*0.9 = 0.675, so you will end up voting for both of
            # these Proposals
            #
            # A Zargham work of art.
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
    """
    The function before has told us how much each Participant has decided to
    increase his nonvesting_holdings.

    The Participant will distribute his tokens across the Proposals that he
    supports, proportional to his affinity to each Proposal.

    But this function is not just about the participants. The function before
    has told us what are the new conviction values for each candidate Proposal.
    If they're below a minimum value, then the Proposal is marked as failed.
    """
    network = s['network']
    candidates = get_proposals(network, status=ProposalStatus.CANDIDATE)
    proposals_supported = _input['proposals_supported']
    alpha = params[0]['alpha']
    min_support = params[0]['min_supp']

    # Update the participants holdings
    participants = get_participants(network)
    for i in participants:
        network.nodes[i]['item'].holdings_nonvesting.value += _input["delta_holdings"][i]
        supported = proposals_supported[i]
        total_affinity = np.sum(
            [network.edges[(i, j)]['affinity'] for j in supported])
        for j in candidates:
            if j in supported:
                normalized_affinity = network.edges[(
                    i, j)]['affinity']/total_affinity
                network.edges[(i, j)]['tokens'] = normalized_affinity * \
                    network.nodes[i]['item'].holdings_nonvesting.value
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
            network.nodes[j]['item'].status = ProposalStatus.FAILED
    return ("network", network)
