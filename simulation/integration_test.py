import pandas as pd
from cadCAD.configuration import Experiment
from cadCAD.configuration.utils import config_sim
from cadCAD.engine import ExecutionContext, ExecutionMode, Executor
from cadCAD import configs

import unittest
import numpy as np
import copy

from utils import (new_probability_func, new_exponential_func, new_gamma_func,
                   new_random_number_func, new_choice_func)
from hatch import create_token_batches, Commons
from simrunner import get_simulation_results, run_simulation
from network_utils import (bootstrap_network, get_participants,
                           get_edges_by_type, get_proposals_conviction_list)
from simulation import (bootstrap_simulation, CommonsSimulationConfiguration,
                        partial_state_update_blocks)


class TestParticipant(unittest.TestCase):
    def setUp(self):
        c = CommonsSimulationConfiguration(random_seed=1)
        results, df_final = get_simulation_results(c)
        self.df_final = df_final

    def test_participant_token_batch_age_is_updated_every_timestep(self):
        """
        Test that the age of the Participants' token batch is updated every
        timestep. The test checks if the older token batch age has the same
        age
        of the simulation (timestep). It considers that at least one
        participant stays in the commons from the beginning to the end of the
        simulation.
        """
        for index, row in self.df_final.iterrows():
            timestep = row["timestep"]
            network = row["network"]
            participants = get_participants(network)

            participants_token_batch_ages = []
            for i, participant in participants:
                participants_token_batch_ages.append(
                                            participant.holdings.age_days)
            # Check if the older token batch has the same age of the simulation
            self.assertEqual(max(participants_token_batch_ages), timestep)


class TestProposal(unittest.TestCase):
    def setUp(self):
        c = CommonsSimulationConfiguration(random_seed=1)
        df = run_simulation(c)
        self.df = df

    def test_conviction_is_updated_once_by_timestep(self):
        """
        Test that the Proposals' conviction is updated only once by timestep.
        First, it creates a new column on the result Data Frame with the psub
        labels, and then checks the behavior of each psub. Only the psub
        "Calculate proposals' conviction" updated the proposals' convictions.
        The psubs "Generate new participants" and "Generate new proposals" add
        new participants and proposals to the network, but should not affect
        the conviction of existing proposals. The psub
        "Participant decides if he wants to exit" removes participants from
        the network, thus it might remove proposals created by the removed
        participants. This psub should not affect the remaining proposals'
        conviction. The other psubs should not affect the proposals'
        conviction.

        Reminder: Currently on the code the proposals that become active,
        failed or completed are still having their convictions calculated.
        """
        psubs = partial_state_update_blocks
        # Mapping the substep order to the PSUB label
        psub_map = {order+1: psub['label'] for (order,
                                                psub) in enumerate(psubs)}

        # Add a column with the psub executed on each sustep
        self.df['psubs'] = self.df.substep.map(psub_map)

        for index, row in self.df.iterrows():
            timestep = row["timestep"]
            psub = row["psubs"]
            network = row["network"]

            conviction_list = get_proposals_conviction_list(network)

            if timestep == 0:
                prior_conviction_list = copy.deepcopy(conviction_list)
            if (psub == "Generate new participants" or
                    psub == "Generate new proposals"):
                len_diff = len(conviction_list) - len(prior_conviction_list)
                prior_conviction_list = prior_conviction_list + [0] * len_diff
                self.assertEqual(sorted(conviction_list),
                                 sorted(prior_conviction_list))
            elif psub == "Calculate proposals' conviction":
                # Checks that no proposal have been added or removed
                self.assertEqual(len(conviction_list),
                                 len(prior_conviction_list))
                self.assertFalse(conviction_list == prior_conviction_list)
            elif psub == "Participant decides if he wants to exit":
                self.assertTrue(set(conviction_list) <=
                                set(prior_conviction_list))
            else:
                self.assertEqual(conviction_list, prior_conviction_list)

            prior_conviction_list = copy.deepcopy(conviction_list)
