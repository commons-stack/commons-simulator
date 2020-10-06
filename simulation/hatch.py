from typing import List, Tuple
from abcurve import AugmentedBondingCurve
from datetime import datetime
from collections import namedtuple
from utils import attrs


def vesting_curve(day: int, cliff_days: int, halflife_days: float) -> float:
    """
    The vesting curve includes the flat cliff, and the halflife curve where tokens are gradually unlocked.
    It looks like _/--
    """
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


def hatch_raise_split_pools(total_hatch_raise, hatch_tribute) -> Tuple[float, float]:
    """Splits the hatch raise between the funding / collateral pool based on the fraction."""
    funding_pool = hatch_tribute * total_hatch_raise
    collateral_pool = total_hatch_raise * (1-hatch_tribute)
    return funding_pool, collateral_pool


def create_token_batches(hatcher_contributions: List[int], desired_token_price: float, vesting_80p_unlocked: int) -> Tuple[List[float], float]:
    """
    hatcher_contributions: a list of hatcher contributions in DAI/ETH/whatever
    desired_token_price: used to determine the initial token supply
    vesting_80p_unlocked: vesting parameter - the number of days after which 80% of tokens will be unlocked, including the cliff period
    """
    total_hatch_raise = sum(hatcher_contributions)
    initial_token_supply = total_hatch_raise / desired_token_price

    # In the hatch, everyone buys in at the same time, with the same price. So just split the token supply amongst the hatchers proportionally to their contributions
    tokens_per_hatcher = [(x / total_hatch_raise) *
                          initial_token_supply for x in hatcher_contributions]

    cliff_days, halflife_days = convert_80p_to_cliff_and_halflife(
        vesting_80p_unlocked)
    token_batches = [TokenBatch(
        x, VestingOptions(cliff_days, halflife_days)) for x in tokens_per_hatcher]
    return token_batches, initial_token_supply


VestingOptions = namedtuple("VestingOptions", "cliff_days halflife_days")


class TokenBatch:
    def __init__(self, vesting: float, nonvesting: float, vesting_options=None):
        self.vesting = vesting
        self.nonvesting = nonvesting
        self.vesting_spent = 0

        self.age_days = 0

        self.cliff_days = 0 if not vesting_options else vesting_options.cliff_days
        self.halflife_days = 0 if not vesting_options else vesting_options.halflife_days

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, attrs(self))

    @property
    def total(self):
        return (self.vesting - self.vesting_spent) + self.nonvesting

    def __bool__(self):
        if self.total > 0:
            return True
        return False

    def __add__(self, other):
        total_vesting = self.vesting + other.vesting
        total_nonvesting = self.nonvesting + other.nonvesting
        return total_vesting, total_nonvesting

    def __sub__(self, other):
        total_vesting = self.vesting - other.vesting
        total_nonvesting = self.nonvesting - other.nonvesting
        return total_vesting, total_nonvesting

    def update_age(self, iterations: int = 1):
        """
        Adds the number of iterations to TokenBatch.age_days
        """
        self.age_days += iterations
        return self.age_days

    def unlocked_fraction(self) -> float:
        """
        returns what fraction of the TokenBatch is unlocked to date
        """
        if self.cliff_days and self.halflife_days:
            u = vesting_curve(self.age_days,
                              self.cliff_days, self.halflife_days)
            return u if u > 0 else 0
        else:
            return 1.0

    def spend(self, x: float):
        """
        checks if you can spend so many tokens, then decreases this TokenBatch
        instance's value accordingly
        """
        if x > self.spendable():
            raise Exception("Not so many tokens are available for you to spend yet ({})".format(
                self.age_days))

        y = x - self.nonvesting
        if y > 0:
            self.vesting_spent += y
            self.nonvesting = 0
        else:
            self.nonvesting = abs(y)

        return self.vesting, self.vesting_spent, self.nonvesting

    def spendable(self) -> float:
        """
        spendable() = (self.unlocked_fraction * self.vesting - self.vesting_spent) + self.nonvesting
        Needed in case some Tokens were burnt before.
        """
        return ((self.unlocked_fraction() * self.vesting) - self.vesting_spent) + self.nonvesting


class Commons:
    def __init__(self, total_hatch_raise, token_supply, hatch_tribute=0.2, exit_tribute=0, kappa=2):
        # a fledgling commons starts out in the hatching phase. After the hatch phase ends, money from new investors will only go into the collateral pool.
        # Essentials
        self.hatch_tribute = hatch_tribute
        # (1-0.35) -> 0.65 * total_hatch_raise = 65% collateral, 35% funding
        self._collateral_pool = (1-hatch_tribute) * total_hatch_raise
        self._funding_pool = hatch_tribute * \
            total_hatch_raise  # 0.35 * total_hatch_raise = 35%
        self._token_supply = token_supply
        # hatch_tokens keeps track of the number of tokens that were created when hatching, so we can calculate the unlocking of those
        self._hatch_tokens = token_supply
        self.bonding_curve = AugmentedBondingCurve(
            self._collateral_pool, token_supply, kappa=kappa)

        # Options
        self.exit_tribute = exit_tribute

    def deposit(self, dai):
        """
        Deposit DAI after the hatch phase. This means all the incoming deposit goes to the collateral pool.
        """
        tokens, realized_price = self.bonding_curve.deposit(
            dai, self._collateral_pool, self._token_supply)
        self._token_supply += tokens
        self._collateral_pool += dai
        return tokens, realized_price

    def burn(self, tokens):
        """
        Burn tokens, with/without an exit tribute.
        """
        dai, realized_price = self.bonding_curve.burn(
            tokens, self._collateral_pool, self._token_supply)
        self._token_supply -= tokens
        self._collateral_pool -= dai
        money_returned = dai

        if self.exit_tribute:
            self._funding_pool += self.exit_tribute * dai
            money_returned = (1-self.exit_tribute) * dai

        return money_returned, realized_price

    def dai_to_tokens(self, dai):
        """
        Given the size of the common's collateral pool, return how many tokens would x DAI buy you.
        """
        price = self.bonding_curve.get_token_price(self._collateral_pool)
        return dai / price

    def token_price(self):
        """
        Query the bonding curve for the current token price, given the size of the commons's collateral pool.
        """
        return self.bonding_curve.get_token_price(self._collateral_pool)

    def spend(self, amount):
        """
        Decreases the Common's funding_pool by amount.
        Raises an exception if this would make the funding pool negative.
        """
        if self._funding_pool - amount < 0:
            raise Exception("{} funds requested but funding pool only has {}".format(
                amount, self._funding_pool))
        self._funding_pool -= amount
        return
