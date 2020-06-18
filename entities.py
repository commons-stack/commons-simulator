import numpy as np
from hatch import TokenBatch


class Participant:
    def __init__(self, holdings_vesting: TokenBatch = None, holdings_nonvesting: TokenBatch = None):
        self.name = "Somebody"
        self.sentiment = np.random.rand()
        self.holdings_vesting = holdings_vesting
        self.holdings_nonvesting = holdings_nonvesting

    def __repr__(self):
        return "{}, holdings_vesting: {}, holdings_nonvesting: {}".format(self.sentiment, self.holdings_vesting, self.holdings_vesting)


class Proposal:
    def __init__(self, funds_requested: int, trigger_func):
        self.conviction = 0
        self.status = "candidate"
        self.age = 0
        self.funds_requested = funds_requested
        self.trigger = trigger_func

    def __repr__(self):
        return "status: {}, age: {}, funds_requested: {}".format(self.status, self.age, self.funds_requested)
