import numpy as np
from hatch import TokenBatch
from enum import Enum
from convictionvoting import trigger_threshold
from english_words import english_words_set
import random


class Participant:
    def __init__(self, holdings_vesting: TokenBatch = None, holdings_nonvesting: TokenBatch = None):
        self.name = "Somebody"
        self.sentiment = np.random.rand()
        self.holdings_vesting = holdings_vesting
        self.holdings_nonvesting = holdings_nonvesting

    def __repr__(self):
        return "<{} {}, holdings_vesting: {}, holdings_nonvesting: {}>".format(self.__class__.__name__, self.sentiment, self.holdings_vesting, self.holdings_vesting)


ProposalStatus = Enum("ProposalStatus", "CANDIDATE ACTIVE COMPLETED FAILED")
# candidate: proposal is being evaluated by the commons
# active: has been approved and is funded
# completed: the proposal was effective/successful
# failed: did not get to active status or failed after funding


class Proposal:
    def __init__(self, funds_requested: int, trigger: float):
        self.name = "{} {}".format(
            random.choice(list(english_words_set)),
            random.choice(list(english_words_set)))
        self.conviction = 0
        self.status = ProposalStatus.CANDIDATE
        self.age = 0
        self.funds_requested = funds_requested
        self.trigger = trigger

    def __repr__(self):
        return "<{} \"{}\" status: {}, age: {}, funds_requested: {}, conviction: {}>".format(self.__class__.__name__, self.name, self.status, self.age, self.funds_requested, self.conviction)

    def update_age(self):
        self.age += 1
        return self.age

    def update_threshold(self, funding_pool, token_supply):
        if self.status == ProposalStatus.CANDIDATE:
            self.trigger = trigger_threshold(
                self.funds_requested, funding_pool, token_supply)
        return self.trigger
