import unittest
from unittest.mock import patch, MagicMock
import networkx as nx

from convictionvoting import trigger_threshold
from entities import Participant, Proposal
import network_utils


def are_there_nonzero_values_in_dict(dictionary):
    """
    Example:
    {'delta_holdings': {0: 0.13405269115654075,
        1: 0, 2: 0, 3: 0.24943837481994094, 4: 0}}
    should report 0: True, 3: True
    """
    answer = False
    for i in dictionary:
        answer = answer or bool(dictionary[i])
    return answer


"""
As much as possible, make all software components deterministic.

In cases where it is impossible to do so, it actually isn't so important to
check that y happens x% of the time. What is important is that it lets us access
the code easily, independent of other components.

Remember: a model is just a theory. We write tests not to verify the model, but
we do need to know that it is working as intended and we need to be able to dive in
quickly if there is a problem.
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
        Test that the function works. If we set the probability to 1, all Participants should buy in.
        If we set the probability to 0, no Participants should buy in.
        """

        state = {
            "network": self.network,
        }

        with patch('network_utils.probability') as mock:
            mock.return_value = True
            answer = network_utils.participants_more_likely_to_buy_with_high_sentiment(
                self.params, 1, 1, state)
            print(are_there_nonzero_values_in_dict(
                answer["delta_holdings"]), answer["delta_holdings"])

            self.assertTrue(all(answer["delta_holdings"].values()))

        with patch('network_utils.probability') as mock:
            mock.return_value = False
            answer = network_utils.participants_more_likely_to_buy_with_high_sentiment(
                self.params, 1, 1, state)
            print(are_there_nonzero_values_in_dict(
                answer["delta_holdings"]), answer["delta_holdings"])

            self.assertFalse(any(answer["delta_holdings"].values()))


if __name__ == '__main__':
    unittest.main()
