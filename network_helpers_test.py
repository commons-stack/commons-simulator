import unittest
from network_helpers import get_proposals, get_participants
import networkx as nx
from entities import Proposal, Participant


class TestNetworkUtils(unittest.TestCase):
    def setUp(self):
        self.network = nx.DiGraph()
        for i in range(10):
            self.network.add_node(i, item=Participant())
        for i in range(5):
            self.network.add_node(i, item=Proposal(500, 5))

    def test_get_proposals(self):
        proposals = get_proposals(self.network)
        for i in proposals:
            self.assertIsInstance(self.network.nodes[i]["item"], Proposal)


if __name__ == '__main__':
    unittest.main()
