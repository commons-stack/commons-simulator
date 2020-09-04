from abcurve import AugmentedBondingCurve, invariant, supply, spot_price, mint, withdraw
import unittest


class TestOriginalEquations(unittest.TestCase):
    def test_magnitude_orders(self):
        # The equations are supposed to be used with 1 (million).
        # But this makes things impractical from a programming perspective because you don't want to remember which variable is denoted in units what.
        # Hopefully things work just the same if you put in 1000,000,000 instead of 1e3.
        r = 10000
        s = 1000000
        kappa = 2
        i = invariant(r, s, kappa)
        print(i)


class TestAugmentedBondingCurve(unittest.TestCase):
    def test_get_token_supply(self):
        # R = 1, S0 = 1, V0 = 1.0, kappa = 2 should give this data:
        # [0 1 2 3 4 5 6 7 8 9] -> [0.0, 1.0, 1.4142135623730951, 1.7320508075688772, 2.0, 2.23606797749979, 2.449489742783178, 2.6457513110645907, 2.8284271247461903, 3.0]
        abc = AugmentedBondingCurve(1, 1, kappa=2)
        self.assertEqual(abc.get_token_supply(1), 1)

        self.assertEqual(abc.get_token_supply(2), 1.4142135623730951)

    def test_get_token_price(self):
        # [0 1 2 3 4 5 6 7 8 9] -> [0.0, 0.02, 0.0282842712474619, 0.034641016151377546, 0.04, 0.044721359549995794, 0.04898979485566356, 0.052915026221291815, 0.0565685424949238, 0.06]
        abc = AugmentedBondingCurve(1, 1, kappa=2)
        self.assertEqual(abc.get_token_price(1), 2.0)

        self.assertEqual(abc.get_token_price(2), 2.8284271247461903)

    def test_deposit(self):
        abc = AugmentedBondingCurve(1, 1, kappa=2)
        old_current_reserve = 1
        old_token_supply = 1
        # print(abc)
        # Deposit 4 million DAI, given that the current reserve pool is 1 million DAI and there are 1 million tokens
        tokens, realized_price = abc.deposit(4, 1, 1)
        print("The current price is", realized_price,
              "and you will get", tokens, "million tokens")
        self.assertEqual(tokens, 1.2360679774997898)
        self.assertEqual(realized_price, 3.2360679774997894)

    def test_burn(self):
        abc = AugmentedBondingCurve(1, 1, kappa=2)

        dai_million_returned, realized_price = abc.burn(0.5, 1, 1)
        self.assertEqual(dai_million_returned, 0.75)
        self.assertEqual(realized_price, 1.5)
