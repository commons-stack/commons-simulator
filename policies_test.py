import unittest
from unittest.mock import patch

from hatch import Commons, TokenBatch, VestingOptions
from network_utils import bootstrap_network
from policies import GenerateNewParticipant, GenerateNewProposal


class TestGenerateNewParticipant(unittest.TestCase):
    def setUp(self):
        self.commons = Commons(10000, 1000)
        self.sentiment = 0.5

    def test_p_randomly(self):
        """
        Simply test that the code runs.
        """
        state = {
            "commons": self.commons,
            "sentiment": self.sentiment
        }
        with patch("policies.probability") as p:
            p.return_value = True
            ans = GenerateNewParticipant.p_randomly(None, 0, 0, state)
            self.assertEqual(ans["new_participant"], True)
            self.assertIsNotNone(ans["new_participant_investment"])
            self.assertIsNotNone(ans["new_participant_tokens"])

    def test_su_add_to_network(self):
        """
        Test that the state update function did add the Participant to the
        network, and that the network maintained its integrity (i.e. all edges
        were properly setup)
        """
        with patch("network_utils.influence") as p:
            p.return_value = 0.8
            n_old = bootstrap_network([TokenBatch(1000, VestingOptions(10, 30))
                            for _ in range(4)], 1, 3000, 4e6)
            import ipdb; ipdb.set_trace()
            n_old_len = len(n_old.nodes)

            _input = {
                "new_participant": True,
                "new_participant_investment": 16.872149388283283,
                "new_participant_tokens": 1.0545093367677052
            }
            _, n_new = GenerateNewParticipant.su_add_to_network(None, 0, 0, {"network": n_old}, _input)
            n_new_len = len(n_new.nodes)
            print(n_new.nodes(data="item"))

            self.assertEqual(n_old_len, 5)
            self.assertEqual(n_new_len, 6)
            self.assertEqual(n_new.nodes(data="item")[5].holdings_nonvesting.value, 1.0545093367677052)
