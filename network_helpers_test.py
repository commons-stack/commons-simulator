import unittest

import networkx as nx

from convictionvoting import trigger_threshold
from entities import Participant, Proposal
from network_helpers import (
    get_proposals, participants_more_likely_to_buy_with_high_sentiment)


def are_there_nonzero_values_in_dict(dictionary):
    """
    Example:
    {'delta_holdings': {0: 0.13405269115654075, 1: 0, 2: 0, 3: 0.24943837481994094, 4: 0}}
    should report 0: True, 3: True
    """
    answer = False
    for i in dictionary:
        answer = answer or bool(dictionary[i])
    return answer


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


"""
When writing tests for a non-deterministic system, we don't really need to check
that y happens x% of the time. What is important is that it lets us access the
code easily, independent of other components.
"""


class ParticipantsActingTest(unittest.TestCase):
    def setUp(self):
        self.params = {
            0: {
                "sentiment_decay": 0.01,
                "trigger_threshold": trigger_threshold,
                "min_proposal_age_days": 2,
                "sentiment_sensitivity": 0.75,
                "alpha": 0.5,
                'min_supp': 50,
            }
        }

        self.network = nx.DiGraph()

        for i in range(10):
            p = Participant()
            p.sentiment = 1.0
            self.network.add_node(i, item=p)

    def test_participants_more_likely_to_buy_with_high_sentiment(self):
        """
        If we set their sentiment to max 1.0, Participants should buy in 30% of the time
        """
        state = {
            "network": self.network,
        }

        yes_there_were_nonzero_values = 0
        for _ in range(10):
            answer = participants_more_likely_to_buy_with_high_sentiment(
                self.params, 1, 1, state)
            print(are_there_nonzero_values_in_dict(
                answer["delta_holdings"]), answer["delta_holdings"])

            if are_there_nonzero_values_in_dict(answer["delta_holdings"]):
                yes_there_were_nonzero_values += 1

        self.assertGreaterEqual(yes_there_were_nonzero_values, 3)


if __name__ == '__main__':
    unittest.main()
