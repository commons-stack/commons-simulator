import unittest

import networkx as nx

from entities import Participant, Proposal, ProposalStatus
from network_utils import get_participants, get_proposals, get_edges_by_type


class TestNetworkUtils(unittest.TestCase):
    def setUp(self):
        self.network = nx.DiGraph()

        for i in range(0, 10, 2):
            self.network.add_node(i, item=Participant())
            self.network.add_node(i+1, item=Proposal(10, 5))

        n_count = len(self.network.nodes)
        for i in range(n_count):
            for j in range(n_count):
                if not(j == i):
                    self.network.add_edge(i, j)
                    self.network.edges[(i, j)]["type"] = "support"

    def test_get_participants(self):
        res = get_participants(self.network)
        self.assertEqual(len(res), 5)

    def test_get_proposals(self):
        res = get_proposals(self.network)
        self.assertEqual(len(res), 5)

        proposal = Proposal(10, 5)
        proposal.status = ProposalStatus.ACTIVE
        self.network.add_node(len(self.network.nodes), item=proposal)

        res = get_proposals(self.network, status=ProposalStatus.ACTIVE)
        self.assertEqual(len(res), 1)

    def test_get_edges_by_type(self):
        res = get_edges_by_type(self.network, "support")
        self.assertEqual(len(res), 90)
