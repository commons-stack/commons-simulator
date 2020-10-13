# value function for a given state (reserve,supply)
def invariant(reserve, supply, kappa):
    return (supply**kappa)/reserve

# given a value function (parameterized by kappa)
# and an invariant coefficient invariant
# return Supply supply as a function of reserve


def supply(reserve, kappa, invariant):
    return (invariant*reserve)**(1/kappa)

# given a value function (parameterized by kappa)
# and an invariant coeficient invariant
# return a spot price P as a function of reserve


def spot_price(reserve, kappa, invariant):
    return kappa*reserve**((kappa-1)/kappa)/invariant**(1/kappa)

# for a given state (reserve,supply)
# given a value function (parameterized by kappa)
# and an invariant coeficient invariant
# deposit d_reserve to Mint d_supply
# with realized price d_reserve/d_supply


def mint(d_reserve, reserve, supply, kappa, invariant):
    d_supply = (invariant*(reserve+d_reserve))**(1/kappa)-supply
    realized_price = d_reserve/d_supply
    return d_supply, realized_price

# for a given state (reserve,supply)
# given a value function (parameterized by kappa)
# and an invariant coeficient invariant
# burn d_supply to Withdraw d_reserve
# with realized price d_reserve/d_supply


def withdraw(d_supply, reserve, supply, kappa, invariant):
    d_reserve = reserve-((supply-d_supply)**kappa)/invariant
    realized_price = d_reserve/d_supply
    return d_reserve, realized_price


class AugmentedBondingCurve:
    def __init__(self, reserve_initial, token_supply_initial, kappa=2):
        """Create a stateless bonding curve.

        reserve_initial (DAI)
        token_supply_initial (DAI)
        kappa (the exponent part of the curve, default is 2)
        """
        self.kappa = kappa
        self.invariant = invariant(
            reserve_initial, token_supply_initial, kappa)

    def __repr__(self):
        return "ABC Kappa: {}, Invariant: {}".format(self.kappa, self.invariant)

    def deposit(self, dai, current_reserve, current_token_supply):
        # Returns number of new tokens minted, and their realized price
        tokens, realized_price = mint(
            dai, current_reserve, current_token_supply, self.kappa, self.invariant)
        return tokens, realized_price

    def burn(self, tokens_millions, current_reserve, current_token_supply):
        # Returns number of DAI that will be returned (excluding exit tribute) when the user burns their tokens, with their realized price
        dai, realized_price = withdraw(
            tokens_millions, current_reserve, current_token_supply, self.kappa, self.invariant)
        return dai, realized_price

    def get_token_price(self, current_reserve):
        return spot_price(current_reserve, self.kappa, self.invariant)

    def get_token_supply(self, current_reserve):
        return supply(current_reserve, self.kappa, self.invariant)
