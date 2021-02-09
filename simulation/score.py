import math
from typing import NamedTuple

from network_utils import get_participants, get_proposals, ProposalStatus
from simulation import CommonsSimulationConfiguration


class CommonsScore(object):
    """
        Calculates a final score for a commons simulation run.
    """

    def __init__(self, params: CommonsSimulationConfiguration, df_final, sigma=112, multiplier_token_price=2):
        self.params = params
        self.df_final = df_final
        self.sigma = sigma
        self.metrics: Metrics = None
        self.multiplier_token_price = multiplier_token_price

    def calc_final_price_ratio(self) -> float:
        '''
            Calculates the ratio between final price compared to hatch price
        '''
        hatch_price = self.df_final.iloc[0, :]['token_price']
        final_price = self.df_final.iloc[-1, :]['token_price']            
        final_price_ratio = final_price / (self.multiplier_token_price * hatch_price)
        # Penalty if final price is smaller than 80% of the hatch price
        if final_price < 0.8 * hatch_price:
            return -0.5
        else:
            return final_price_ratio if final_price_ratio < 1 else 1

    def calc_avg_price_to_initial_ratio(self) -> float:
        '''
            Calculates the average price compared with hatch price
        '''
        hatch_price = self.df_final.iloc[0, :]['token_price']
        avg_price = self.df_final['token_price'].mean()
        #  Penalty if average price is smaller than hatch price
        if avg_price < hatch_price:
            return -0.5
#         return avg_price / hatch_price
        avg_price_ratio = (avg_price - hatch_price) / (self.multiplier_token_price * self.df_final['token_price'].std())
        return avg_price_ratio if avg_price_ratio < 1 else 1

    def calc_funded_proposals_ratio(self) -> float:
        '''
            Calculates the number of proposals funded compared to
            initial proposals
        '''
        init_proposals = self.params.proposals
#         funded = self.metrics.candidates + self.metrics.actives + self.metrics.completed + self.metrics.failed
        funded = self.metrics.actives + self.metrics.completed + self.metrics.failed
#         return funded / init_proposals
        funded_proposals_ratio = (funded - init_proposals) / (5 * funded)
        return funded_proposals_ratio if funded_proposals_ratio < 1 else 1

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
        funds_spent_ratio =  (total_spent - hatch_funds) / total_spent
        return funds_spent_ratio if funds_spent_ratio < 1 else 1

    def calc_avg_funds_to_initial_ratio(self) -> float:
        '''
            Calculates the ration between  average amount in funding pool
            over time compared to the amount received in the hatch phase
        '''
        hatch_funds = self.df_final.iloc[0, :]['funding_pool']
        avg_funds = self.df_final['funding_pool'].mean()
        avg_funds_ratio = avg_funds / hatch_funds
        return avg_funds_ratio if avg_funds_ratio < 1 else 1
#         return (avg_funds - hatch_funds) / self.df_final['funding_pool'].std()

    def calc_final_sentiment(self) -> float:
        '''
            Obtains the final sentiment at the end of the simulation
        '''
        final_sentiment = self.df_final.iloc[-1, :]['sentiment']
        if final_sentiment < 0.75:
            return -0.5
        return final_sentiment if final_sentiment < 1 else 1

    def calc_avg_sentiment(self) -> float:
        '''
            Obtains the average sentiment
        '''
        avg_sentiment = self.df_final['sentiment'].mean()
        min_sentiment = self.df_final['sentiment'].min()
        if min_sentiment < 0.5:
            return -0.5
        return avg_sentiment if avg_sentiment < 1 else 1

    def calc_success_to_failed_ratio(self) -> float:
        '''
            Calculates the ratio of successful projects to failed ones
        '''
        success_to_failed_ratio = self.metrics.completed / self.metrics.failed
        return success_to_failed_ratio if success_to_failed_ratio < 1 else 1

    def calc_participant_to_hatchers_ratio(self) -> float:
        '''
            Calculates the ratio between No of final participants and No of hatchers
        '''
        hatchers = self.params.hatchers
        participants_ratio = self.metrics.participants / hatchers
        return participants_ratio if participants_ratio < 1 else 1

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
