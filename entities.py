import random
import uuid
from enum import Enum
from inspect import getmembers
from os.path import abspath
from types import FunctionType

import numpy as np
from english_words import english_words_set

import config
from config import sentiment_sensitivity
from convictionvoting import trigger_threshold
from hatch import TokenBatch
from utils import probability


"""
Helper functions from
https://stackoverflow.com/questions/192109/is-there-a-built-in-function-to-print-all-the-current-properties-and-values-of-a
to print all attributes of a class without me explicitly coding it out.
"""


def api(obj):
    return [name for name in dir(obj) if name[0] != '_']


def attrs(obj):
    disallowed_properties = {
        name for name, value in getmembers(type(obj))
        if isinstance(value, (property, FunctionType))}
    return {
        name: getattr(obj, name) for name in api(obj)
        if name not in disallowed_properties and hasattr(obj, name)}


class Participant:
    def __init__(self, holdings_vesting: TokenBatch = None, holdings_nonvesting: TokenBatch = None):
        self.name = "Somebody"
        self.sentiment = np.random.rand()
        self.holdings_vesting = holdings_vesting
        self.holdings_nonvesting = holdings_nonvesting

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, attrs(self))

    def buy(self) -> float:
        """
        If the Participant decides to buy more tokens, returns the number of
        tokens. Otherwise, return 0.

        This method does not modify itself, it simply returns the answer so that
        cadCAD's state update functions will make the changes and maintain its
        functional-ness.
        """
        engagement_rate = 0.3 * self.sentiment
        force = self.sentiment - config.sentiment_sensitivity
        if probability(engagement_rate) and force > 0:
            delta_holdings = np.random.rand() * force
            return delta_holdings
        return 0

    def sell(self) -> float:
        """
        Decides to sell some tokens, and if so how many. If the Participant
        decides to sell some tokens, returns the number of tokens. Otherwise,
        return 0.

        This method does not modify itself, it simply returns the answer so that
        cadCAD's state update functions will make the changes and maintain its
        functional-ness.
        """
        engagement_rate = 0.3 * self.sentiment
        force = self.sentiment - config.sentiment_sensitivity
        if probability(engagement_rate) and force < 0:
            delta_holdings = np.random.rand() * force
            return delta_holdings
        return 0

    def create_proposal(self, total_funds_requested, median_affinity, funding_pool) -> bool:
        """
        Here the Participant will decide whether or not to create a new
        Proposal.

        This equation, originally from randomly_gen_new_proposal(), is a
        systems-type simulation. An individual Participant would likely think in
        a different way, and thus this equation should change. Nevertheless for
        simplicity's sake, we use this same equation for now.

        Explanation: If the median affinity is high, the Proposal Rate should be
        high.

        If total funds_requested in candidate proposals is much lower than the
        funding pool (i.e. the Commons has lots of spare money), then people are
        just going to pour in more Proposals.
        """
        percent_of_funding_pool_being_requested = total_funds_requested/funding_pool
        proposal_rate = median_affinity / \
            (1 + percent_of_funding_pool_being_requested)
        new_proposal = probability(proposal_rate)
        return new_proposal

    def vote_on_candidate_proposals(self, candidate_proposals: dict) -> dict:
        """
        Here the Participant decides which Candidate Proposals he will stake
        tokens on. This method does not decide how many tokens he will stake
        on them, because another function should decide how the tokens should be
        balanced across the newly supported proposals and the ones the
        Participant already supported.

        Copied from
        participants_buy_more_if_they_feel_good_and_vote_for_proposals()

        candidate dict format:
        {
            "proposalUUID": affinity,
            ...
        }

        NOTE: the original cadCAD policy returned {'delta_holdings':
        delta_holdings, 'proposals_supported': proposals_supported}
        proposals_supported seems to include proposals ALREADY supported by the
        participant, but I don't think it is needed.
        """
        new_voted_proposals = {}
        engagement_rate = .3*self.sentiment
        if probability(engagement_rate):
            # Put your tokens on your favourite Proposals, where favourite is
            # calculated as 0.75 * (the affinity for the Proposal you like the
            # most) e.g. if there are 2 Proposals that you have affinity 0.8,
            # 0.9, then 0.75*0.9 = 0.675, so you will end up voting for both of
            # these Proposals
            #
            # A Zargham work of art.
            for candidate in candidate_proposals:
                affinity = candidate_proposals[candidate]
                # Hardcoded 0.75 instead of a configurable sentiment_sensitivity
                # because modifying sentiment_sensitivity without changing the
                # hardcoded cutoff value of 0.5 may cause unintended behaviour.
                # Also, 0.75 is a reasonable number in this case.
                cutoff = 0.75 * np.max(list(candidate_proposals.values()))
                if cutoff < .5:
                    cutoff = .5

                if affinity > cutoff:
                    new_voted_proposals[candidate] = affinity

        return {'new_voted_proposals': new_voted_proposals}


ProposalStatus = Enum("ProposalStatus", "CANDIDATE ACTIVE COMPLETED FAILED")
# candidate: proposal is being evaluated by the commons
# active: has been approved and is funded
# completed: the proposal was effective/successful
# failed: did not get to active status or failed after funding


class Proposal:
    def __init__(self, funds_requested: int, trigger: float):
        self.uuid = uuid.uuid4()
        self.conviction = 0
        self.status = ProposalStatus.CANDIDATE
        self.age = 0
        self.funds_requested = funds_requested
        self.trigger = trigger

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, attrs(self))

    def update_age(self):
        self.age += 1
        return self.age

    def update_threshold(self, funding_pool: float, token_supply: float):
        if self.status == ProposalStatus.CANDIDATE:
            self.trigger = trigger_threshold(
                self.funds_requested, funding_pool, token_supply)
        else:
            self.trigger = np.nan
        return self.trigger

    def has_enough_conviction(self, funding_pool: float, token_supply: float):
        """
        It's just a conviction < threshold check, but we recalculate the
        trigger_threshold so that the programmer doesn't have to remember to run
        update_threshold before running this method.
        """
        if self.status == ProposalStatus.CANDIDATE:
            threshold = trigger_threshold(
                self.funds_requested, funding_pool, token_supply)
            if self.conviction < threshold:
                return False
            return True
        else:
            raise(Exception(
                "Proposal {} is not a Candidate Proposal and so asking it if it will pass is inappropriate".format(self.name)))
