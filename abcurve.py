#value function for a given state (R,S)
def invariant(R,S,kappa):
    return (S**kappa)/R

#given a value function (parameterized by kappa)
#and an invariant coeficient V0
#return Supply S as a function of reserve R
def supply(R, kappa, V0):
    return (V0*R)**(1/kappa)

#given a value function (parameterized by kappa)
#and an invariant coeficient V0
#return a spot price P as a function of reserve R
def spot_price(R, kappa, V0):
    return kappa*R**((kappa-1)/kappa)/V0**(1/kappa)

#for a given state (R,S)
#given a value function (parameterized by kappa)
#and an invariant coeficient V0
#deposit deltaR to Mint deltaS
#with realized price deltaR/deltaS
def mint(deltaR, R,S, kappa, V0):
    deltaS = (V0*(R+deltaR))**(1/kappa)-S
    realized_price = deltaR/deltaS
    return deltaS, realized_price

#for a given state (R,S)
#given a value function (parameterized by kappa)
#and an invariant coeficient V0
#burn deltaS to Withdraw deltaR
#with realized price deltaR/deltaS
def withdraw(deltaS, R,S, kappa, V0):
    deltaR = R-((S-deltaS)**kappa)/V0
    realized_price = deltaR/deltaS
    return deltaR, realized_price

class AugmentedBondingCurve:
    def __init__(self, initial_reserve, initial_token_supply, kappa=2):
        """Create a stateful bonding curve.

        initial_reserve (millions of DAI)
        initial_token_supply (millions)
        kappa (the exponent part of the curve, default is 2)
        """
        self.initial_reserve = initial_reserve
        self.initial_token_supply = initial_token_supply
        
        self.current_reserve = self.initial_reserve
        self.current_token_supply = self.initial_token_supply
        
        self.kappa = kappa
        self.invariant = (self.initial_token_supply**kappa) / self.initial_reserve

    def __repr__(self):
        return "ABC Reserve {} million; Token_Supply {} million; Current Token Price {}".format(self.current_reserve, self.current_token_supply, self.get_token_price())

    def deposit(self, dai_million):
        # Returns number of new tokens minted, and their realized price
        tokens, realized_price = mint(dai_million, self.current_reserve, self.current_token_supply, self.kappa, self.invariant)
        
        self.current_reserve += dai_million
        self.current_token_supply += tokens
        return tokens, realized_price

    def burn(self, tokens_million):
        # Returns number of DAI that will be returned (excluding exit tribute) when the user burns their tokens, with their realized price
        dai_million, realized_price = withdraw(tokens_million, self.current_reserve, self.current_token_supply, self.kappa, self.invariant)
        self.current_reserve -= dai_million
        self.current_token_supply -= tokens_million
        return dai_million, realized_price

    def get_token_price(self):
        return spot_price(self.current_reserve, self.kappa, self.invariant)
    
    def get_token_supply(self):
        return supply(self.current_reserve, self.kappa, self.invariant)
