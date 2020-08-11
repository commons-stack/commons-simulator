import unittest
from unittest.mock import patch

import networkx as nx

from entities import Participant, Proposal, ProposalStatus
from network_utils import (get_edges_by_type, get_participants, get_proposals,
                           setup_conflict_edges, setup_influence_edges)


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

    def test_setup_influence_edges_multiple(self):
        """
        Test that the code works, and that edges are created between DIFFERENT
        nodes. Also ensures that edges refer to the node index, not the Participant
        object stored within the node.
        """
        with patch('network_utils.influence') as mock:
            mock.return_value = 0.5
            self.network = setup_influence_edges(self.network)
            edges = get_edges_by_type(self.network, "influence")
            print(edges)
            self.assertEqual(len(edges), 20)
            for e in edges:
                self.assertIsInstance(e[0], int)
                self.assertIsInstance(e[1], int)
                self.assertNotEqual(e[0], e[1])

    def test_setup_influence_edges_single(self):
        with patch('network_utils.influence') as mock:
            mock.return_value = 0.5
            self.network = setup_influence_edges(self.network, participant=0)
            edges = get_edges_by_type(self.network, "influence")
            print(edges)
            self.assertEqual(len(edges), 4)
            for e in edges:
                self.assertIsInstance(e[0], int)
                self.assertIsInstance(e[1], int)
                self.assertNotEqual(e[0], e[1])

    def test_setup_conflict_edges_multiple(self):
        """
        Test that the code works, and that edges are created between DIFFERENT
        nodes. Also ensures that edges refer to the node index, not the Proposal
        object stored within the node.
        """
        self.network = setup_conflict_edges(self.network, rate=1)
        edges = get_edges_by_type(self.network, "conflict")

        self.assertEqual(len(edges), 20)
        for e in edges:
            self.assertIsInstance(e[0], int)
            self.assertIsInstance(e[1], int)
            self.assertNotEqual(e[0], e[1])

    def test_setup_conflict_edges_single(self):
        """
        Test that the code works, and that edges are created between DIFFERENT
        nodes. Also ensures that edges refer to the node index, not the Proposal
        object stored within the node.
        """
        proposal_count = len(get_proposals(self.network))

        self.network = setup_conflict_edges(self.network, 1, rate=1)
        edges = get_edges_by_type(self.network, "conflict")

        self.assertEqual(len(edges), proposal_count-1)
        for e in edges:
            self.assertIsInstance(e[0], int)
            self.assertIsInstance(e[1], int)
            self.assertNotEqual(e[0], e[1])
