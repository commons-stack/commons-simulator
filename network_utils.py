from typing import List
import numpy as np
import networkx as nx
from hatch import TokenBatch
from scipy.stats import expon, gamma
from entities import Participant, Proposal, ProposalStatus
from convictionvoting import trigger_threshold


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


def add_hatchers_to_network(participants: List[TokenBatch]) -> nx.DiGraph:
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
