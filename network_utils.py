from typing import Dict, List

import networkx as nx
import numpy as np
from scipy.stats import expon, gamma

from convictionvoting import trigger_threshold
from entities import Participant, Proposal, ProposalStatus
from hatch import TokenBatch


def get_edges_by_type(network, edge_type_selection):
    def filter_by_type(n1, n2):
        if network.edges[(n1, n2)]["type"] == edge_type_selection:
            return True
        return False

    view = nx.subgraph_view(network, filter_edge=filter_by_type)
    return view.edges()


def get_proposals(network, status: ProposalStatus = None):
    def filter_proposal(n):
        if isinstance(network.nodes[n]["item"], Proposal):
            if status:
                return network.nodes[n]["item"].status == status
            return True
        return False

    view = nx.subgraph_view(network, filter_node=filter_proposal)
    return view.nodes(data="item")


def get_participants(network) -> Dict[int, Participant]:
    def filter_participant(n):
        if isinstance(network.nodes[n]["item"], Participant):
            return True
        return False
    view = nx.subgraph_view(network, filter_node=filter_participant)
    return view.nodes(data="item")


def create_network(participants: List[TokenBatch]) -> nx.DiGraph:
    """
    Creates a new DiGraph with Participants corresponding to the input
    TokenBatches.
    """
    network = nx.DiGraph()
    for i, p in enumerate(participants):
        p_instance = Participant(
            holdings_vesting=p, holdings_nonvesting=TokenBatch(0))
        network.add_node(i, item=p_instance)
    return network


def influence(scale=1, sigmas=3):
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

    influence_rv = expon.rvs(loc=0.0, scale=scale)
    if influence_rv > scale+sigmas*scale**2:
        return influence_rv
    return None


def setup_influence_edges(network: nx.DiGraph, participant=None) -> nx.DiGraph:
    """
    Calculates the chances that a Participant is influential enough to have an
    'influence' edge in the network to other Participants, and creates the
    corresponding edge in the graph.

    Takes an optional participant argument, which is the index number of the
    Participant in network.nodes. If this argument is present, it will setup the
    influence edges only for this Participant.
    """
    def loop_over_other_participants(network, participants, i):
        for other_participant in participants:
            if not(other_participant == i):
                influence_rv = influence()
                if influence_rv:
                    network.add_edge(i, other_participant)
                    network.edges[(i, other_participant)
                                  ]['influence'] = influence_rv
                    network.edges[(i, other_participant)]['type'] = 'influence'
        return network
    # Turn it into a dict to make a copy out of the View, because the View
    # changes whenever we add edges to the graph, which results in RuntimeError:
    # dictionary changed size during iteration
    participants = dict(get_participants(network))

    # Do not use "if not participant" - index number 0 will evaluate to False.
    if participant is None:
        for i in participants:
            n = loop_over_other_participants(network, participants, i)
        return n

    return loop_over_other_participants(network, participants, participant)


def setup_conflict_edges(network: nx.DiGraph, proposal=None, rate=.25) -> nx.DiGraph:
    """
    Supporting one Proposal may mean going against another Proposal, in which
    case a Proposal-Proposal conflict edge is created. This function calculates
    the chances of that happening and the 'strength' of such a conflict.

    Takes an optional proposal argument, which is the index number of the
    Proposal in network.nodes. If this argument is present, it will setup the
    conflict edges only for this Proposal.
    """
    def loop_over_other_proposals(network, proposals, proposal):
        for other_proposal in proposals:
            if not(other_proposal == proposal):
                # (rate=0.25) means 25% of other Proposals are going to conflict
                # with this particular Proposal. And when they do conflict, the
                # conflict number is high (at least 1 - 0.25 = 0.75).
                conflict_rv = np.random.rand()
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
            n = loop_over_other_proposals(network, proposals, i)
        return n
    return loop_over_other_proposals(network, proposals, proposal)


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

        n = setup_conflict_edges(n, rate=.25)
        n = setup_influence_edges(n)
    return n
