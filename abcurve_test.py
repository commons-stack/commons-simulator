from abcurve import AugmentedBondingCurve
import unittest

class TestAugmentedBondingCurve(unittest.TestCase):
    def test_get_token_supply(self):
        # R = 1, S0 = 1, V0 = 1.0, kappa = 2 should give this data:
        # [0 1 2 3 4 5 6 7 8 9] -> [0.0, 1.0, 1.4142135623730951, 1.7320508075688772, 2.0, 2.23606797749979, 2.449489742783178, 2.6457513110645907, 2.8284271247461903, 3.0]
        abc = AugmentedBondingCurve(1, 1, kappa=2)
        self.assertEqual(abc.get_token_supply(), 1)

        abc.current_reserve = 2
        self.assertEqual(abc.get_token_supply(), 1.4142135623730951)
    
    def test_get_token_price(self):
        # [0 1 2 3 4 5 6 7 8 9] -> [0.0, 0.02, 0.0282842712474619, 0.034641016151377546, 0.04, 0.044721359549995794, 0.04898979485566356, 0.052915026221291815, 0.0565685424949238, 0.06]
        abc = AugmentedBondingCurve(1, 1, kappa=2)
        self.assertEqual(abc.get_token_price(), 2.0)

        abc.current_reserve = 2
        self.assertEqual(abc.get_token_price(), 2.8284271247461903)
    
    def test_deposit(self):
        abc = AugmentedBondingCurve(1, 1, kappa=2)
        old_current_reserve = abc.current_reserve
        old_token_supply = abc.current_token_supply
        # print(abc)
        tokens, realized_price = abc.deposit(4)
        # print("The current price is", realized_price, "and you will get", tokens, "million tokens")
        self.assertEqual(abc.current_token_supply, old_token_supply + tokens)
        self.assertEqual(abc.current_reserve, old_current_reserve + 4)
        # print(abc)
    
    def test_burn(self):
        abc = AugmentedBondingCurve(1, 1, kappa=2)
        
        dai_million_returned, realized_price = abc.burn(0.5)
        self.assertEqual(dai_million_returned, 0.75)
        self.assertEqual(realized_price, 1.5)

        self.assertEqual(abc.current_reserve, 0.25)
        self.assertEqual(abc.current_token_supply, 0.5)
        self.assertLess(abc.current_reserve, abc.initial_reserve)
        self.assertLess(abc.current_token_supply, abc.initial_token_supply)