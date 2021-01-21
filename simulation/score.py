import math
from typing import NamedTuple

from network_utils import get_participants, get_proposals, ProposalStatus
from simulation import CommonsSimulationConfiguration


class CommonsScore(object):
    """
        Calculates a final score for a commons simulation run.
    """

    def __init__(self, params: CommonsSimulationConfiguration, df_final, sigma=100):
        self.params = params
        self.df_final = df_final
        self.sigma = sigma
        self.metrics: Metrics = None

    def calc_price_ratio(self) -> float:
        '''
            Calculates the ratio between price compared to hatch price
        '''
        hatch_price = self.df_final.iloc[0, :]['token_price']
        final_price = self.df_final.iloc[-1, :]['token_price']
        return final_price / hatch_price

    def calc_avg_price_to_initial_ratio(self) -> float:
        '''
            Calculates the average price compared with hatch price
        '''
        hatch_price = self.df_final.iloc[0, :]['token_price']
        avg_price = self.df_final['token_price'].mean()
#         return avg_price / hatch_price
        return (avg_price - hatch_price) / self.df_final['token_price'].std()

    def calc_funded_proposals_ratio(self) -> float:
        '''
            Calculates the number of proposals funded compared to 
            initial proposals
        '''
        init_proposals = self.params.proposals
#         funded = self.metrics.candidates + self.metrics.actives + self.metrics.completed + self.metrics.failed
        funded = self.metrics.actives + self.metrics.completed + self.metrics.failed
#         return funded / init_proposals
        return (funded - init_proposals) / funded

    def calc_funds_spent_ratio(self) -> float:
        '''
            Calculates the total spent by the funding pool compared to 
            the amount received in the hatch phase
        '''
        hatch_funds = self.df_final.iloc[0, :]['funding_pool']
#         total_spent = self.metrics.funds_candidates + self.metrics.funds_actives + self.metrics.funds_completed + self.metrics.funds_failed
        total_spent = self.metrics.funds_actives + \
            self.metrics.funds_completed + self.metrics.funds_failed
#         return total_spent / hatch_funds
        return (total_spent - hatch_funds) / total_spent

    def calc_avg_funds_to_initial_ratio(self) -> float:
        '''
            Calculates the ration between  average amount in funding pool 
            over time compared to the amount received in the hatch phase
        '''
        hatch_funds = self.df_final.iloc[0, :]['funding_pool']
        avg_funds = self.df_final['funding_pool'].mean()
        return avg_funds / hatch_funds
#         return (avg_funds - hatch_funds) / self.df_final['funding_pool'].std()

    def calc_final_sentiment(self) -> float:
        '''
            Obtains the final sentiment at the end of the simulation
        '''
        return self.df_final.iloc[-1, :]['sentiment']

    def calc_avg_sentiment(self) -> float:
        '''
            Obtains the average sentiment
        '''
        return self.df_final['sentiment'].mean()

    def calc_success_to_failed_ratio(self) -> float:
        '''
            Calculates the ratio of successful projects to failed ones
        '''
        return self.metrics.completed / self.metrics.failed

    def calc_participant_to_hatchers_ratio(self) -> float:
        '''
            Calculates the ratio between No of final participants and No of hatchers
        '''
        hatchers = self.params.hatchers
        return self.metrics.participants / hatchers

    def eval(self) -> float:
        '''
            Calculates the final score using all the defined metrics methods in this class
        '''
        last_network = self.df_final.iloc[-1, 0]
        p_candidates = get_proposals(
            last_network, status=ProposalStatus.CANDIDATE)
        candidates = len(p_candidates)
        p_actives = get_proposals(last_network, status=ProposalStatus.ACTIVE)
        actives = len(p_actives)
        p_completed = get_proposals(
            last_network, status=ProposalStatus.COMPLETED)
        completed = len(p_completed)
        p_failed = get_proposals(last_network, status=ProposalStatus.FAILED)
        failed = len(p_failed)
        participants = len(get_participants(last_network))

        funds_candidates = sum([p.funds_requested for _, p in p_candidates])
        funds_actives = sum([p.funds_requested for _, p in p_actives])
        funds_completed = sum([p.funds_requested for _, p in p_completed])
        funds_failed = sum([p.funds_requested for _, p in p_failed])

        self.metrics = Metrics(participants=participants,
                               candidates=candidates,
                               funds_candidates=funds_candidates,
                               actives=actives,
                               funds_actives=funds_actives,
                               completed=completed,
                               funds_completed=funds_completed,
                               failed=failed,
                               funds_failed=funds_failed
                               )
        methods = [attr for attr in dir(self) if callable(
            getattr(self, attr)) and attr.startswith('calc_')]
        return round(sum([getattr(self, method)() for method in methods]) * self.sigma)


class Metrics(NamedTuple):
    participants: int
    candidates: int
    funds_candidates: float
    actives: int
    funds_actives: float
    completed: int
    funds_completed: float
    failed: int
    funds_failed: float
