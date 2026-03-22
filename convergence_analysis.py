import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import numpy as np
from scipy.stats import norm
import pandas as pd
from main import option_data, market_data, tree


def check_dividend(market_data):
    """Check if there are dividends. Returns True if dividend exists."""
    return hasattr(market_data, 'D') and market_data.D != 0


class ConvergenceVisualizer:
    """Class to visualize the convergence of tree pricing to Black-Scholes price."""

    def __init__(self):
        """Initialize the visualizer with zoom scale parameter."""
        self.zoom_scale = 1.1
        self.data = None
        self.ax = None

    def generate_data(self, steps_range):
        """
        Generate convergence data comparing tree and Black-Scholes prices.

        Args:
            steps_range: Range of number of steps to test

        Returns:
            pandas.DataFrame: Contains number of steps and corresponding prices
        """
        # Check for dividends first
        if check_dividend(market_data):
            print(
                "Impossible de comparer avec Black-Scholes : "
                "des dividendes ont été détectés.\n"
                "La formule classique de Black-Scholes ne prend "
                "pas en compte les dividendes."
            )
            return None

        data = {
            'Nombre de Pas': [],
            'Prix Arbre': [],
            'Prix Black-Scholes': []
        }

        time_to_maturity = option_data.time

        # Calculate Black-Scholes price
        bs_price = self._calculate_bs_price(time_to_maturity)

        print(
            f"Calcul de la convergence pour l'option "
            f"{'Call' if option_data.is_call else 'Put'}..."
        )

        # Calculate tree price for each number of steps
        for steps in steps_range:
            print(f"Traitement de {steps} pas...")
            tree_price = self._calculate_tree_price(steps, time_to_maturity)

            # Store results
            data['Nombre de Pas'].append(steps)
            data['Prix Arbre'].append(tree_price)
            data['Prix Black-Scholes'].append(bs_price)

            # Memory cleanup
            tree.release_tree_memory()

        return pd.DataFrame(data)

    def _calculate_bs_price(self, time_to_maturity):
        """Calculate Black-Scholes price for the given parameters."""
        # Calculate d1 and d2
        d1 = (
                     np.log(market_data.StartPrice / option_data.strike) +
                     (market_data.r + market_data.sigma ** 2 / 2) * time_to_maturity
             ) / (market_data.sigma * np.sqrt(time_to_maturity))
        d2 = d1 - market_data.sigma * np.sqrt(time_to_maturity)

        # Calculate discounted strike
        discount = np.exp(-market_data.r * time_to_maturity)
        discounted_strike = option_data.strike * discount

        if option_data.is_call:
            return (market_data.StartPrice * norm.cdf(d1) -
                    discounted_strike * norm.cdf(d2))
        else:
            return (discounted_strike * norm.cdf(-d2) -
                    market_data.StartPrice * norm.cdf(-d1))

    def _calculate_tree_price(self, steps, time_to_maturity):
        """Calculate tree price for given number of steps."""
        # Update tree configuration
        delta_t = time_to_maturity / steps
        tree.nbsteps = steps
        tree.delta_t = delta_t
        market_data.df = np.exp(-market_data.r * delta_t)

        # Build tree and calculate price
        tree.build_tree(option_data, market_data)
        from A_main_Pricer import Pricer
        pricer = Pricer(root=tree.root, option=option_data, market=market_data)
        return pricer.price()

    def on_scroll(self, event):
        """
        Handle mouse wheel scrolling for zoom functionality.

        Args:
            event: Mouse scroll event containing coordinates and direction
        """
        if not event.inaxes:
            return

        # Get current axis limits and mouse position
        cur_xlim = event.inaxes.get_xlim()
        cur_ylim = event.inaxes.get_ylim()
        x_data = event.xdata
        y_data = event.ydata

        # Calculate zoom scale based on scroll direction
        scale_factor = (
            self.zoom_scale if event.button == 'up' else 1 / self.zoom_scale
        )

        # Calculate new dimensions
        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

        # Calculate relative position for centered zoom
        rel_x = (cur_xlim[1] - x_data) / (cur_xlim[1] - cur_xlim[0])
        rel_y = (cur_ylim[1] - y_data) / (cur_ylim[1] - cur_ylim[0])

        # Update plot limits
        event.inaxes.set_xlim([
            x_data - new_width * (1 - rel_x),
            x_data + new_width * rel_x
        ])
        event.inaxes.set_ylim([
            y_data - new_height * (1 - rel_y),
            y_data + new_height * rel_y
        ])
        plt.draw()

    def reset_zoom(self, event):
        """Reset zoom to show the full data range with margins."""
        # Reset x-axis limits
        self.ax.set_xlim(0, 100)

        # Calculate y-axis limits with margins
        ymin = min(
            self.data['Prix Arbre'].min(),
            self.data['Prix Black-Scholes'].min()
        )
        ymax = max(
            self.data['Prix Arbre'].max(),
            self.data['Prix Black-Scholes'].max()
        )
        margin = (ymax - ymin) * 0.1
        self.ax.set_ylim(ymin - margin, ymax + margin)

        plt.draw()

    def visualize(self, data):
        """
        Create and display the convergence visualization.

        Args:
            data: DataFrame containing pricing data to visualize
        """
        # Check if data is available (no dividends case)
        if data is None:
            return

        self.data = data

        # Setup figure
        fig = plt.figure(figsize=(12, 8))

        # Create title with option parameters
        title_params = self._get_title_parameters()
        fig.suptitle(title_params, fontsize=12, y=0.95)

        # Create price convergence plot
        self._create_convergence_plot()

        # Initialize view
        self.reset_zoom(None)

        # Add reset zoom button
        self._add_reset_button(fig)

        # Setup mouse wheel zoom
        fig.canvas.mpl_connect('scroll_event', self.on_scroll)

        plt.tight_layout()
        plt.show()

    def _get_title_parameters(self):
        """Create title string with option parameters."""
        option_type = "Call" if option_data.is_call else "Put"
        exercise_type = "Américaine" if option_data.is_american else "Européenne"

        return (
            f"Option {exercise_type} {option_type}\n"
            f"S0={market_data.StartPrice}, K={option_data.strike}, "
            f"r={market_data.r * 100}%, σ={market_data.sigma * 100}%"
        )

    def _create_convergence_plot(self):
        """Create the main convergence plot."""
        self.ax = plt.subplot2grid((6, 1), (0, 0), rowspan=5)
        self.ax.plot(
            self.data['Nombre de Pas'],
            self.data['Prix Arbre'],
            'b-',
            label='Prix Arbre',
            linewidth=2
        )
        self.ax.plot(
            self.data['Nombre de Pas'],
            self.data['Prix Black-Scholes'],
            'r-',
            label='Prix BS',
            linewidth=2
        )
        self.ax.set_title(
            'Convergence du Prix Arbre vers le Prix Black-Scholes'
        )
        self.ax.grid(True)
        self.ax.legend()

    def _add_reset_button(self, fig):
        """Add reset zoom button to the figure."""
        button_ax = plt.subplot2grid((6, 1), (5, 0))
        reset_button = Button(button_ax, 'Réinitialiser Zoom')
        reset_button.on_clicked(self.reset_zoom)


def main():
    """Main execution function."""
    # Initialize visualizer
    viz = ConvergenceVisualizer()

    # Generate convergence data
    steps_range = range(1, 101)
    data = viz.generate_data(steps_range)

    # Display visualization if data is available
    if data is not None:
        viz.visualize(data)


if __name__ == "__main__":
    main()