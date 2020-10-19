import unittest
from unittest.mock import patch

import networkx as nx

from entities import Participant, Proposal, ProposalStatus
from hatch import TokenBatch, VestingOptions
from network_utils import (add_proposal, bootstrap_network, calc_avg_sentiment,
                           calc_median_affinity, calc_total_affinity, calc_total_conviction,
                           calc_total_funds_requested, get_edges_by_type, get_edges_by_participant_and_type,
                           get_participants, get_proposals,
                           setup_conflict_edges, setup_influence_edges_bulk,
                           setup_influence_edges_single, setup_support_edges)


class TestNetworkUtils(unittest.TestCase):
    def setUp(self):
        self.network = nx.DiGraph()

        for i in range(0, 10, 2):
            self.network.add_node(i, item=Participant(TokenBatch(0, 0)))
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

    def test_get_edges_by_participant_and_type(self):
        self.network = setup_support_edges(self.network)
        res = get_edges_by_participant_and_type(self.network, 0, "support")

        # Assert that Participant 0 has support edges to all other Proposals
        # (1,3,5,7,9)
        for i in [1, 3, 5, 7, 9]:
            self.assertIn(i, res)
            self.assertEqual(res[i]["type"], "support")

    def test_setup_influence_edges_bulk(self):
        """
        Test that the code works, and that edges are created between DIFFERENT
        nodes. Also ensures that edges refer to the node index, not the Participant
        object stored within the node.
        """
        with patch('network_utils.influence') as mock:
            mock.return_value = 0.5
            self.network = setup_influence_edges_bulk(self.network)
            edges = get_edges_by_type(self.network, "influence")
            self.assertEqual(len(edges), 20)
            for e in edges:
                self.assertIsInstance(e[0], int)
                self.assertIsInstance(e[1], int)
                self.assertNotEqual(e[0], e[1])

    def test_setup_influence_edges_bulk_wont_overwrite_existing_influences(self):
        """
        Test that setup_influence_edges_bulk will not overwrite existing
        influence edges.
        """
        with patch('network_utils.influence') as mock:
            mock.return_value = 0.5
            self.network = setup_influence_edges_bulk(self.network)
            edges = get_edges_by_type(self.network, "influence")
            self.assertEqual(len(edges), 20)
            for e in edges:
                self.assertEqual(self.network.get_edge_data(
                    e[0], e[1])["influence"], 0.5)

            mock.return_value = 0.8
            self.network = setup_influence_edges_bulk(self.network)
            edges = get_edges_by_type(self.network, "influence")
            self.assertEqual(len(edges), 20)
            for e in edges:
                self.assertEqual(self.network.get_edge_data(
                    e[0], e[1])["influence"], 0.5)

    def test_setup_influence_edges_single(self):
        """
        Test that the code works, and that if I set up influence edges for a
        Participant in a network where he has 4 peers, 8 edges will be created,
        4 from the new Participant to the existing Participants + 4 from
        the existing Participants to the new Participant
        """
        with patch('network_utils.influence') as mock:
            mock.return_value = 0.5
            self.network = setup_influence_edges_single(self.network, 0)
            edges = list(get_edges_by_type(self.network, "influence"))
            self.assertEqual(len(edges), 8)
            for e in edges:
                self.assertIsInstance(e[0], int)
                self.assertIsInstance(e[1], int)
                self.assertNotEqual(e[0], e[1])

            # Test that Participant 0 has 4 edges to other Participants, and
            # that other Participants (like Participant 2) only have 1 edge to
            # Participant 0.
            a = tuple(zip(*edges))
            self.assertEqual(a[0].count(0), 4)
            self.assertEqual(a[0].count(2), 1)
            self.assertEqual(a[1].count(0), 4)
            self.assertEqual(a[1].count(2), 1)

    def test_setup_influence_edges_single_wont_overwrite_existing_influences(self):
        """
        Test that setup_influence_edges_single will not overwrite existing
        influence edges.
        """
        with patch('network_utils.influence') as mock:
            mock.return_value = 0.5
            self.network = setup_influence_edges_single(self.network, 0)
            edges = list(get_edges_by_type(self.network, "influence"))
            self.assertEqual(len(edges), 8)

            # First, check that the influence edges all have the original
            # influence value of 0.5
            for e in edges:
                self.assertEqual(self.network.get_edge_data(
                    e[0], e[1])["influence"], 0.5)

            # Now, ensure that the original influence value of 0.5 was not
            # overwritten with 0.8
            mock.return_value = 0.8
            self.network = setup_influence_edges_single(self.network, 0)
            edges = list(get_edges_by_type(self.network, "influence"))
            self.assertEqual(len(edges), 8)
            for e in edges:
                self.assertEqual(self.network.get_edge_data(
                    e[0], e[1])["influence"], 0.5)

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
        network = bootstrap_network(token_batches, 1, 3000, 4e6, 0.2)

        edges = list(network.edges(data="type"))
        _, _, edge_types = list(zip(*edges))

        self.assertEqual(edge_types.count('support'), 4)
        self.assertEqual(len(get_participants(network)), 4)
        self.assertEqual(len(get_proposals(network)), 1)

    def test_calc_total_funds_requested(self):
        sum = calc_total_funds_requested(self.network)
        self.assertEqual(sum, 50)

    def test_calc_median_affinity_network_with_no_support_edges(self):
        with self.assertRaises(Exception):
            calc_median_affinity(self.network)

    def test_add_proposal(self):
        """
        This test ensures that the Proposal was added and that
        setup_conflict_edges() was executed for that particular node.
        """
        n1, j = add_proposal(self.network, Proposal(23, 111))
        self.assertEqual(n1.nodes[j]["item"].funds_requested, 23)
        self.assertEqual(n1.nodes[j]["item"].trigger, 111)

        self.assertEqual(len(n1.edges), 5)
        for u, v, t in n1.edges(data="type"):
            self.assertEqual(v, 10)
            self.assertEqual(t, "support")
            self.assertIn(u, [0, 2, 4, 6, 8])

    def test_calc_total_conviction(self):
        """
        Ensure that the function reports the correct sum of conviction from all
        support edges.
        """
        self.network = setup_support_edges(self.network)
        ans = calc_total_conviction(self.network, 1)
        self.assertEqual(ans, 0)

        support_edges = get_edges_by_type(self.network, "support")

        # Every support edge gets a conviction value. Since there are 5
        # Participants and 5 Proposals, this should result in a sum of 5
        # conviction for each Proposal.
        for u, v in support_edges:
            self.network.edges[u, v]["conviction"] = 1

        for i in [1, 3, 5, 7, 9]:
            ans = calc_total_conviction(self.network, i)
            self.assertEqual(ans, 5)

    def test_calc_total_affinity(self):
        """
        Ensure that the affinities in the support edges add up to >0 (since they
        are randomly generated, they won't be 0)
        """
        self.network = setup_support_edges(self.network)
        ans = calc_total_affinity(self.network)
        self.assertNotEqual(ans, 0)

    def test_calc_avg_sentiment(self):
        """
        Ensure that the average sentiment was calculated correctly
        """
        participants = get_participants(self.network)

        for _, p in participants:
            p.sentiment = 0.5
        self.assertEqual(0.5, calc_avg_sentiment(self.network))

        for _, p in participants:
            p.sentiment = 1
        self.assertEqual(1, calc_avg_sentiment(self.network))

        for _, p in participants:
            p.sentiment = 1
        self.network.nodes[8]["item"].sentiment = 0.5
        self.assertEqual(0.9, calc_avg_sentiment(self.network))
