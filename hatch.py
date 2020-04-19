from typing import List, Tuple
from abcurve import AugmentedBondingCurve
from datetime import datetime

def unlocked_fraction(day: int, cliff_days: int, halflife_days: float) -> float:
    return 1 - 0.5**((day - cliff_days)/halflife_days)

def convert_80p_to_cliff_and_halflife(days: int, v_ratio: int = 2) -> Tuple[float, float]:
    """
    For user's convenience, we ask him after how many days he would like 80% of his tokens to be unlocked.
    This needs to be converted into a half life (unit days).
    2.321928094887362 is log(base0.5) 0.2, or log 0.2 / log 0.5.
    v_ratio is cliff / halflife, and its default is determined by Commons Stack
    """
    halflife = days / (2.321928094887362 + v_ratio)
    cliff = v_ratio * halflife
    return cliff, halflife

def hatch_raise_split_pools(total_hatch_raise, funding_pool_fraction):
    """Splits the hatch raise between the funding / collateral pool based on the fraction."""
    funding_pool = funding_pool_fraction * total_hatch_raise
    collateral_pool = total_hatch_raise * (1-funding_pool_fraction)
    return funding_pool, collateral_pool

def contributions_to_token_batches(hatcher_contributions: List[int], initial_token_supply: int, vesting_80p_unlocked: int) -> List[float]:
    """
    hatcher_contributions: a list of hatcher contributions
    initial_token_supply: NOT denominated in millions
    vesting_80p_unlocked: vesting parameter - the number of days after which 80% of tokens will be unlocked, including the cliff period
    """
    total_hatch_raise = sum(hatcher_contributions)

    # In the hatch, everyone buys in at the same time, with the same price. So just split the token supply amongst the hatchers proportionally to their contributions
    tokens_per_hatcher = [(x / total_hatch_raise) * initial_token_supply for x in hatcher_contributions]

    cliff_days, halflife_days = convert_80p_to_cliff_and_halflife(vesting_80p_unlocked)

    token_batches = [TokenBatch(x, cliff_days, halflife_days, hatch=True) for x in tokens_per_hatcher]
    return token_batches

class TokenBatch:
    def __init__(self, value: float, cliff_days: int, halflife_days: int, hatch = False):
        self.hatch_tokens = hatch
        self.value = value
        self.creation_date = datetime.today()
        self.cliff_days = cliff_days
        self.halflife_days = halflife_days
    def __repr__(self):
        o = "TokenBatch {} {}, Unlocked: {}".format("Hatch" if self.hatch_tokens else "", self.value, self.unlocked(datetime.today()))
        return o

    def unlocked(self, day: datetime = datetime.today()) -> float:
        if self.hatch_tokens:
            days_delta = day - self.creation_date
            u = unlocked_fraction(days_delta.days, self.cliff_days, self.halflife_days)
            return u if u > 0 else 0
        else:
            return 1.0

class Organization:
    def __init__(self, total_hatch_raise, funding_pool_fraction, token_supply_millions, exit_tribute=0):
        # a fledgling organization starts out in the hatching phase. After the hatch phase ends, money from new investors will only go into the collateral pool.
        # Essentials
        self.funding_pool_fraction = funding_pool_fraction
        self._collateral_pool = (1-funding_pool_fraction) * total_hatch_raise  # (1-0.35) -> 0.65 * total_hatch_raise = 65% collateral, 35% funding
        self._funding_pool = funding_pool_fraction * total_hatch_raise  # 0.35 * total_hatch_raise = 35%
        self._token_supply = token_supply_millions
        self._hatch_tokens = token_supply_millions  # hatch_tokens keeps track of the number of tokens that were created when hatching, so we can calculate the unlocking of those
        self.bonding_curve = AugmentedBondingCurve(self._collateral_pool, token_supply_millions)

        # Options
        self.exit_tribute = exit_tribute
    
    def deposit(self, dai_millions):
        """
        Deposit DAI after the hatch phase. This means all the incoming deposit goes to the collateral pool.
        """
        tokens, realized_price = self.bonding_curve.deposit(dai_millions, self._collateral_pool, self._token_supply)
        self._token_supply += tokens
        self._collateral_pool += dai_millions
        return tokens, realized_price

    def burn(self, tokens_millions):
        """
        Burn tokens, with/without an exit tribute.
        """
        dai_millions, realized_price = self.bonding_curve.burn(tokens_millions, self._collateral_pool, self._token_supply)
        self._token_supply -= tokens_millions
        self._collateral_pool -= dai_millions
        money_returned = dai_millions

        if self.exit_tribute:
            self._funding_pool += organization.exit_tribute * dai_millions
            money_returned = (1-organization.exit_tribute) * dai_millions 

        return money_returned, realized_price