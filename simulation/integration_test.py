import pandas as pd
from cadCAD.configuration import Experiment
from cadCAD.configuration.utils import config_sim
from cadCAD.engine import ExecutionContext, ExecutionMode, Executor
from cadCAD import configs

import unittest
import numpy as np

from utils import (new_probability_func, new_exponential_func, new_gamma_func,
                   new_random_number_func, new_choice_func)
from hatch import create_token_batches, Commons
from network_utils import bootstrap_network, get_participants
from simrunner import get_simulation_results
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
        timestep. The test checks if the older token batch age has the same age
        of the simulation (timestep). It considers that at least one
        participant stays in the commons from the beginning to the end of the
        simulation.
        """
        for index, row in self.df_final.iterrows():
            timestep = row['timestep']
            network = row['network']
            participants = get_participants(network)

            participants_token_batch_ages = []
            for i, participant in participants:
                participants_token_batch_ages.append(participant.holdings.age_days)
            # Check if the older token batch has the same age of the simulation
            self.assertEqual(max(participants_token_batch_ages), timestep)
