import math
import time
from dataclasses import dataclass
from A_main_Pricer import Pricer

# Import from main
from main import (
    option_data,
    market_data,
    nb_steps,
    tree,
    pricer
)


@dataclass
class Greeks:
    """Class to hold calculated Greek values"""
    delta: float = 0.0
    gamma: float = 0.0
    vega: float = 0.0
    theta: float = 0.0
    rho: float = 0.0


class GreeksCalculator:
    """
    Calculator for option Greeks using finite difference methods.
    Implements calculations for delta, gamma, vega, theta, and rho.
    """

    def __init__(self, pricer, market_data, option_data, tree):
        """
        Initialize the Greeks calculator with required pricing components.

        Args:
            pricer: Option pricing engine
            market_data: Market parameters
            option_data: Option specifications
            tree: Trinomial tree structure
        """
        self.pricer = pricer
        self.market = market_data
        self.option = option_data
        self.tree = tree
        self.initial_price = self.pricer.price()

    def calculate_all_greeks(self) -> Greeks:
        """
        Calculate all Greeks using appropriate perturbations.

        Returns:
            Greeks: Object containing all calculated Greek values
        """
        start_time = time.time()
        print("Début du calcul des Grecques...")

        # Use same base perturbation as VBA implementation
        base_perturbation = 0.01
        greeks = Greeks()

        # Delta (1% perturbation)
        greeks.delta = self.calculate_delta(base_perturbation)

        # Gamma (perturbation of 3)
        greeks.gamma = self.calculate_gamma(3.0)

        # Vega (1% perturbation)
        greeks.vega = self.calculate_vega(base_perturbation)

        # Theta (1% perturbation)
        greeks.theta = self.calculate_theta(base_perturbation)

        # Rho (1% perturbation)
        greeks.rho = self.calculate_rho(base_perturbation)

        return greeks

    def calculate_delta(self, perturbation: float) -> float:
        """
        Calculate Delta using finite difference method.

        Args:
            perturbation: Size of price perturbation

        Returns:
            float: Calculated Delta value
        """
        original_price = self.market.StartPrice

        # Upward perturbation (Spot + perturbation)
        self.market.StartPrice = original_price + perturbation
        self.tree.delta_t = self.option.time / self.tree.nbsteps
        self.tree.compute_alpha(self.market)
        self.tree.build_tree(self.option, self.market)
        new_pricer = Pricer(self.tree.root, self.option, self.market)
        price_up = new_pricer.price()

        # Downward perturbation (Spot - perturbation)
        self.market.StartPrice = self.market.StartPrice - 2 * perturbation
        self.tree.delta_t = self.option.time / self.tree.nbsteps
        self.tree.compute_alpha(self.market)
        self.tree.build_tree(self.option, self.market)
        new_pricer = Pricer(self.tree.root, self.option, self.market)
        price_down = new_pricer.price()

        # Reset the market price
        self.market.StartPrice = self.market.StartPrice + perturbation

        return (price_up - price_down) / (2 * perturbation)

    def calculate_gamma(self, perturbation: float) -> float:
        """
        Calculate Gamma using finite difference method.

        Args:
            perturbation: Size of price perturbation

        Returns:
            float: Calculated Gamma value
        """
        original_price = self.market.StartPrice

        # Calculate middle price first
        self.tree.delta_t = self.option.time / self.tree.nbsteps
        self.tree.compute_alpha(self.market)
        self.tree.build_tree(self.option, self.market)
        new_pricer = Pricer(self.tree.root, self.option, self.market)
        price_mid = new_pricer.price()

        # Calculate up price
        self.market.StartPrice = original_price + perturbation
        self.tree.delta_t = self.option.time / self.tree.nbsteps
        self.tree.compute_alpha(self.market)
        self.tree.build_tree(self.option, self.market)
        new_pricer = Pricer(self.tree.root, self.option, self.market)
        price_up = new_pricer.price()

        # Calculate down price
        self.market.StartPrice = self.market.StartPrice - 2 * perturbation
        self.tree.delta_t = self.option.time / self.tree.nbsteps
        self.tree.compute_alpha(self.market)
        self.tree.build_tree(self.option, self.market)
        new_pricer = Pricer(self.tree.root, self.option, self.market)
        price_down = new_pricer.price()

        # Reset the market price
        self.market.StartPrice = self.market.StartPrice + perturbation

        return (price_up - 2 * price_mid + price_down) / (perturbation * perturbation)

    def calculate_vega(self, perturbation: float) -> float:
        """
        Calculate Vega using finite difference method.

        Args:
            perturbation: Size of volatility perturbation

        Returns:
            float: Calculated Vega value
        """
        original_vol = self.market.sigma

        # Calculate up price
        self.market.sigma = original_vol + perturbation
        self.tree.delta_t = self.option.time / self.tree.nbsteps
        self.tree.compute_alpha(self.market)
        self.tree.build_tree(self.option, self.market)
        new_pricer = Pricer(self.tree.root, self.option, self.market)
        price_up = new_pricer.price()

        # Calculate down price
        self.market.sigma = original_vol - perturbation
        self.tree.delta_t = self.option.time / self.tree.nbsteps
        self.tree.compute_alpha(self.market)
        self.tree.build_tree(self.option, self.market)
        new_pricer = Pricer(self.tree.root, self.option, self.market)
        price_down = new_pricer.price()

        # Reset volatility
        self.market.sigma = original_vol

        return (price_up - price_down) / (2 * perturbation) * 0.01

    def calculate_theta(self, perturbation: float) -> float:
        """
        Calculate Theta using finite difference method.

        Args:
            perturbation: Size of time perturbation (in days)

        Returns:
            float: Calculated Theta value
        """
        original_time = self.option.time

        # Calculate current price
        self.tree.delta_t = self.option.time / self.tree.nbsteps
        self.tree.compute_alpha(self.market)
        self.tree.build_tree(self.option, self.market)
        new_pricer = Pricer(self.tree.root, self.option, self.market)
        price_current = new_pricer.price()

        # Calculate future price
        self.option.time = original_time - perturbation / 365
        self.tree.delta_t = self.option.time / self.tree.nbsteps
        self.tree.compute_alpha(self.market)
        self.tree.build_tree(self.option, self.market)
        new_pricer = Pricer(self.tree.root, self.option, self.market)
        price_future = new_pricer.price()

        # Reset time
        self.option.time = original_time

        return (price_current - price_future) / perturbation

    def calculate_rho(self, perturbation: float) -> float:
        """
        Calculate Rho using finite difference method.

        Args:
            perturbation: Size of interest rate perturbation

        Returns:
            float: Calculated Rho value
        """
        original_rate = self.market.r
        original_df = self.market.df

        # Calculate up price
        self.market.r = original_rate + perturbation
        self.market.df = math.exp(-self.market.r * self.tree.delta_t)
        self.tree.delta_t = self.option.time / self.tree.nbsteps
        self.tree.compute_alpha(self.market)
        self.tree.build_tree(self.option, self.market)
        new_pricer = Pricer(self.tree.root, self.option, self.market)
        price_up = new_pricer.price()

        # Calculate down price
        self.market.r = original_rate - perturbation
        self.market.df = math.exp(-self.market.r * self.tree.delta_t)
        self.tree.delta_t = self.option.time / self.tree.nbsteps
        self.tree.compute_alpha(self.market)
        self.tree.build_tree(self.option, self.market)
        new_pricer = Pricer(self.tree.root, self.option, self.market)
        price_down = new_pricer.price()

        # Reset rate and discount factor
        self.market.r = original_rate
        self.market.df = original_df

        return (price_up - price_down) / (2 * perturbation)


def main():
    """Main function to run the Greeks calculator and display results."""
    # Initialize calculator with imported data
    calculator = GreeksCalculator(pricer, market_data, option_data, tree)

    # Display parameters
    print(f"\nParamètres de l'Option:")
    print(f"Type: {'Call' if option_data.is_call else 'Put'}")
    print(f"Exercise: {'Américain' if option_data.is_american else 'Européen'}")
    print(f"Strike: {option_data.strike}")
    print(f"Maturité: {option_data.maturity_date}")
    print(f"Temps jusqu'à maturité: {option_data.time:.6f} ans")
    print(f"Nombre d'étapes: {nb_steps}")

    print(f"\nDonnées de Marché:")
    print(f"Prix spot: {market_data.StartPrice}")
    print(f"Taux d'intérêt: {market_data.r:.2%}")
    print(f"Volatilité: {market_data.sigma:.2%}")
    print(f"Dividende: {market_data.D}")
    print(f"Facteur d'actualisation: {market_data.df:.9f}")

    initial_price = pricer.price()
    print(f"\nPrix calculé par l'arbre: {initial_price:.6f}")

    # Calculate Greeks
    greeks = calculator.calculate_all_greeks()

    print("\nGrecques calculées:")
    print(f"Delta: {greeks.delta:.4f}")
    print(f"Gamma: {greeks.gamma:.4f}")
    print(f"Vega: {greeks.vega:.4f}")
    print(f"Theta: {greeks.theta:.4f}")
    print(f"Rho: {greeks.rho:.4f}")


if __name__ == "__main__":
    main()