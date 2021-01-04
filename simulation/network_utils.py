from typing import Dict, List, Tuple

import networkx as nx
import numpy as np
from networkx.classes.reportviews import NodeDataView

from convictionvoting import trigger_threshold
from entities import Participant, ParticipantSupport, Proposal, ProposalStatus
from hatch import TokenBatch


def get_edges_by_type(network: nx.DiGraph, edge_type_selection: str):
    def filter_by_type(n1, n2):
        if network.edges[(n1, n2)]["type"] == edge_type_selection:
            return True
        return False

    view = nx.subgraph_view(network, filter_edge=filter_by_type)
    return view.edges()


def get_edges_by_participant_and_type(network: nx.DiGraph, participant_idx: int, edge_type_selection: str) -> Dict:
    edges_view = network.adj[participant_idx]
    answer = {}
    for key in edges_view:
        if edges_view[key]["type"] == "support":
            answer[key] = edges_view[key]
    return answer


def get_proposals(network: nx.DiGraph, status: ProposalStatus = None):
    def filter_proposal(n):
        if isinstance(network.nodes[n]["item"], Proposal):
            if status:
                return network.nodes[n]["item"].status == status
            return True
        return False

    view = nx.subgraph_view(network, filter_node=filter_proposal)
    return view.nodes(data="item")


def get_participants(network: nx.DiGraph) -> NodeDataView:
    def filter_participant(n):
        if isinstance(network.nodes[n]["item"], Participant):
            return True
        return False
    view = nx.subgraph_view(network, filter_node=filter_participant)
    return view.nodes(data="item")


def add_proposal(network: nx.DiGraph, p: Proposal, random_number_func) -> Tuple[nx.DiGraph, int]:
    j = max(network.nodes) + 1
    network.add_node(j, item=p)
    network = setup_support_edges(network, random_number_func, j)
    return network, j


def add_participant(network: nx.DiGraph, p: Participant, exponential_func, random_number_func) -> Tuple[nx.DiGraph, int]:
    j = max(network.nodes) + 1
    network.add_node(j, item=p)
    network = setup_influence_edges_single(network, j, exponential_func)
    network = setup_support_edges(network, random_number_func, j)
    return network, j


def create_network(token_batches: List[TokenBatch], probability_func, random_number_func) -> nx.DiGraph:
    """
    Creates a new DiGraph with Participants corresponding to the input
    TokenBatches.
    """
    network = nx.DiGraph()
    for i, tb in enumerate(token_batches):
        p_instance = Participant(tb, probability_func, random_number_func)
        # Make the initial participants have sentiments between 0.5 and 1
        p_instance.sentiment = 0.5 + 0.5 * random_number_func()
        network.add_node(i, item=p_instance)
    return network


def influence(exponential_func, scale=1, sigmas=3):
    """
    Calculates the likelihood of one node having influence over another node. If
    so, it returns an influence value, else None.

    expon.rvs with the standard kwargs gives you a lot more values smaller than
    1, but quite a few outliers that could go all the way up to even 8.

    Unless your influence is 3 standard deviations above the norm (where scale
    determines the size of the standard deviation), you don't have any influence
    at all.

    This is broken out so that code that populates the graph initially and code
    that adds new Participants later on can share this code.
    """

    influence_rv = exponential_func(loc=0.0, scale=scale)
    if influence_rv > scale+sigmas*scale**2:
        return influence_rv
    return None


def setup_influence_edges_bulk(network: nx.DiGraph, exponential_func) -> nx.DiGraph:
    """
    Calculates the chances that a Participant is influential enough to have an
    'influence' edge in the network to other Participants, and creates the
    corresponding edge in the graph. If an "influence" type edge already exists,
    it will skip it.

    Takes an optional participant argument, which is the index number of the
    Participant in network.nodes. If this argument is present, it will setup the
    influence edges only for this Participant.
    """
    # Turn it into a dict to make a copy out of the View, because the View
    # changes whenever we add edges to the graph, which results in RuntimeError:
    # dictionary changed size during iteration
    participants = dict(get_participants(network))

    for i in participants:
        for other_participant in participants:
            if not(other_participant == i) and not network.has_edge(i, other_participant):
                influence_rv = influence(exponential_func)
                if influence_rv:
                    network.add_edge(i, other_participant,
                                     influence=influence_rv, type="influence")
    return network


def setup_influence_edges_single(network: nx.DiGraph, participant: int, exponential_func):
    p = dict(get_participants(network))
    del p[participant]
    other_participants = p

    # If we already have Participants at index 0,1,2,3,4 and we added a
    # Participant at index 5, this creates the edges 0,5; 1,5; 2;5 etc.
    for other in other_participants:
        if not network.has_edge(other, participant):
            influence_rv = influence(exponential_func)
            if influence_rv:
                network.add_edge(other, participant,
                                 influence=influence_rv, type="influence")
        if not network.has_edge(participant, other):
            influence_rv = influence(exponential_func)
            if influence_rv:
                network.add_edge(participant, other,
                                 influence=influence_rv, type="influence")
    return network


def setup_conflict_edges(network: nx.DiGraph, random_number_func, proposal=None, rate=.25) -> nx.DiGraph:
    """
    Supporting one Proposal may mean going against another Proposal, in which
    case a Proposal-Proposal conflict edge is created. This function calculates
    the chances of that happening and the 'strength' of such a conflict.

    Takes an optional proposal argument, which is the index number of the
    Proposal in network.nodes. If this argument is present, it will setup the
    conflict edges only for this Proposal.
    """
    def loop_over_other_proposals(network, proposals, proposal, random_number_func):
        for other_proposal in proposals:
            if not(other_proposal == proposal):
                # (rate=0.25) means 25% of other Proposals are going to conflict
                # with this particular Proposal. And when they do conflict, the
                # conflict number is high (at least 1 - 0.25 = 0.75).
                conflict_rv = random_number_func()
                if conflict_rv < rate:
                    network.add_edge(proposal, other_proposal)
                    network.edges[(proposal, other_proposal)
                                  ]['conflict'] = 1-conflict_rv
                    network.edges[(proposal, other_proposal)
                                  ]['type'] = 'conflict'
        return network
    # Turn it into a dict to make a copy out of the View, because the View
    # changes whenever we add edges to the graph, which results in RuntimeError:
    # dictionary changed size during iteration
    proposals = dict(get_proposals(network))

    # Do not use "if not proposal" - index number 0 will evaluate to False.
    if proposal is None:
        for i in proposals:
            network = loop_over_other_proposals(network, proposals, i, random_number_func)
        return network
    return loop_over_other_proposals(network, proposals, proposal, random_number_func)


def setup_support_edges(network: nx.DiGraph, random_number_func, idx=None) -> nx.DiGraph:
    """
    Every Participant has a 'support' edge to every Proposal, and vice versa,
    indicating how much that Participant supports that Proposal. This function
    adds support edges between every Participant and Proposal in the network.

    Takes an optional node index. If the node is a Participant, it will setup
    support edges to other Proposal nodes and vice versa if the node is a
    Proposal.
    """
    def create_support_edge(n, i, j, random_number_func):
        # Token Holder -> Proposal Relationship
        # Looks like Zargham skewed this distribution heavily towards
        # numbers smaller than 0.25 This is the affinity towards proposals.
        # Most Participants won't care about most proposals, but then there
        # will be a few Proposals that they really care about.
        rv = random_number_func()
        a_rv = 1-4*(1-rv)*rv
        n.add_edge(i, j, support=ParticipantSupport(affinity=a_rv, tokens=0, conviction=0), type="support")
        return n
    participants = dict(get_participants(network))
    proposals = dict(get_proposals(network))

    if idx is None:
        for prop in proposals:
            for par in participants:
                network = create_support_edge(network, par, prop, random_number_func)

    else:
        if isinstance(network.nodes[idx]['item'], Proposal):
            for par in participants:
                network = create_support_edge(network, par, idx, random_number_func)
        elif isinstance(network.nodes[idx]['item'], Participant):
            for prop in proposals:
                network = create_support_edge(network, idx, prop, random_number_func)
    return network


def bootstrap_network(n_participants: List[TokenBatch], n_proposals: int, funding_pool: float, token_supply: float, max_proposal_request: float, probability_func, random_number_func, gamma_func, exponential_func) -> nx.DiGraph:
    """
    Convenience function that creates a network ready for simulation in
    the Python notebook in one line.
    """
    n = create_network(n_participants, probability_func, random_number_func)

    for _ in range(n_proposals):
        idx = len(n)
        r_rv = gamma_func(3, loc=0.001, scale=10000)
        n.add_node(idx, item=Proposal(funds_requested=r_rv, trigger=trigger_threshold(
            r_rv, funding_pool, token_supply, max_proposal_request)))

    n = setup_support_edges(n, random_number_func)
    n = setup_conflict_edges(n, random_number_func)
    n = setup_influence_edges_bulk(n, exponential_func)
    return n


def calc_total_funds_requested(network: nx.DiGraph):
    candidates = get_proposals(network, status=ProposalStatus.CANDIDATE)
    fund_requests = [j[1].funds_requested for j in candidates]
    total_funds_requested = np.sum(fund_requests)
    return total_funds_requested


def calc_median_affinity(network: nx.DiGraph):
    supporters = get_edges_by_type(network, 'support')
    if len(supporters) == 0:
        raise Exception("The network has 0 support edges!")

    affinities = [network.edges[e]['support'].affinity for e in supporters]
    median_affinity = np.median(affinities)
    return median_affinity


def calc_total_conviction(network: nx.DiGraph, proposal_idx: int) -> float:
    proposal = network.nodes(data="item")[proposal_idx]
    if not isinstance(proposal, Proposal):
        raise Exception(
            "proposal_idx must point to a node that has a Proposal")

    incoming_edges = network.in_edges(proposal_idx, data="support")
    convictions = [support.conviction for _, _, support in incoming_edges if support]

    return np.sum(convictions)


def calc_total_affinity(network: nx.DiGraph) -> float:
    view = network.edges(data="support")
    affinities = [support.affinity for _, _, support in view]
    return np.sum(affinities)


def calc_avg_sentiment(network: nx.DiGraph) -> float:
    participants = get_participants(network)
    sentiment_total = 0.0
    for _, participant in participants:
        sentiment_total += participant.sentiment

    sentiment_avg = sentiment_total / len(participants)
    return sentiment_avg


def find_in_edges_of_type_for_proposal(network: nx.DiGraph, proposal_idx: int, edge_type: str) -> List[Tuple[int, int, str]]:
    ans = []
    for participant_idx, proposal_idx, t in network.in_edges(proposal_idx, data="type"):
        if t == edge_type:
            ans.append((participant_idx, proposal_idx, edge_type))

    return ans


def get_proposals_conviction_list(network):
    """
    Convenience function. Return a list of proposals' conviction of
    a given network.
    """
    support_edges = get_edges_by_type(network, "support")
    conviction_list = []
    for i, j in support_edges:
        edge = network.edges[i, j]
        conviction = edge["conviction"]
        conviction_list.append(conviction)
    return conviction_list
