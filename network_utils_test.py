import unittest
from unittest.mock import patch

import networkx as nx
from hatch import TokenBatch, VestingOptions
from entities import Participant, Proposal, ProposalStatus
from network_utils import (get_edges_by_type, get_participants, get_proposals,
                           setup_conflict_edges, setup_influence_edges, setup_support_edges, bootstrap_network)


class TestNetworkUtils(unittest.TestCase):
    def setUp(self):
        self.network = nx.DiGraph()

        for i in range(0, 10, 2):
            self.network.add_node(i, item=Participant())
            self.network.add_node(i+1, item=Proposal(10, 5))

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
        self.assertEqual(len(res), 0)

        self.network.add_edge(0, 1, type="support")
        res = get_edges_by_type(self.network, "support")
        self.assertEqual(len(res), 1)

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

    def test_setup_support_edges_multiple(self):
        """
        Tests that support edges are created between every Participant and
        Proposal if no node index is specified.
        """
        network = setup_support_edges(self.network)
        self.assertEqual(len(network.edges), 25)

    def test_setup_support_edges_single_participant(self):
        """
        Tests that a support edge is created to other Proposals when the
        function is fed a node that contains a Participant
        """
        network = setup_support_edges(self.network, 0)
        for i, j in network.edges:
            self.assertEqual(i, 0)
            self.assertIsInstance(network.nodes[i]["item"], Participant)
            self.assertIsInstance(network.nodes[j]["item"], Proposal)

    def test_setup_support_edges_single_proposal(self):
        """
        Tests that a support edge is created to other Participants when the
        function is fed a node that contains a Proposal
        """
        network = setup_support_edges(self.network, 1)
        for i, j in network.edges:
            self.assertEqual(j, 1)
            self.assertIsInstance(network.nodes[i]["item"], Participant)
            self.assertIsInstance(network.nodes[j]["item"], Proposal)

    def test_bootstrap_network(self):
        """
        Tests that the network was created and that the subcomponents work too.
        """
        token_batches = [TokenBatch(1000, VestingOptions(10, 30))
                         for _ in range(4)]
        network = bootstrap_network(token_batches, 1, 3000, 4e6)

        edges = list(network.edges(data="type"))
        _, _, edge_types = list(zip(*edges))

        self.assertEqual(edge_types.count('support'), 4)
        self.assertEqual(len(get_participants(network)), 4)
        self.assertEqual(len(get_proposals(network)), 1)
