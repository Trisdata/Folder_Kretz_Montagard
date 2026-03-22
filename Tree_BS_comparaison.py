import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm
import pandas as pd
from matplotlib.widgets import Button


def check_dividend(market_data):
    """Check if there are dividends. Returns True if dividend exists."""
    return hasattr(market_data, 'D') and market_data.D != 0


def black_scholes_price(s0, k, t, r, sigma, is_call=True):
    """Calculate Black-Scholes price."""
    d1 = (np.log(s0 / k) + (r + sigma ** 2 / 2) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)

    if is_call:
        return s0 * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2)
    else:
        return k * np.exp(-r * t) * norm.cdf(-d2) - s0 * norm.cdf(-d1)


def calculate_slope(prices, strikes, i):
    """Calculate slope using forward difference."""
    if i < len(prices) - 1:
        return (prices[i + 1] - prices[i]) / (strikes[i + 1] - strikes[i])
    return (prices[i] - prices[i - 1]) / (strikes[i] - strikes[i - 1])


class PriceComparisonVisualizer:
    """Class for visualizing price comparisons between Tree and Black-Scholes."""

    def __init__(self):
        """Initialize the visualizer with zoom scale."""
        self.zoom_scale = 1.1
        self.strikes = None
        self.ax1 = None
        self.ax2 = None

    def on_scroll(self, event):
        """Handle mouse wheel scrolling for zoom."""
        if not event.inaxes:
            return

        # Get current axis limits and mouse position
        cur_xlim = event.inaxes.get_xlim()
        cur_ylim = event.inaxes.get_ylim()
        x_data = event.xdata
        y_data = event.ydata

        # Calculate zoom factor
        scale_factor = (self.zoom_scale if event.button == 'up'
                       else 1 / self.zoom_scale)

        # Calculate new dimensions
        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

        # Calculate relative positions
        rel_x = (cur_xlim[1] - x_data) / (cur_xlim[1] - cur_xlim[0])
        rel_y = (cur_ylim[1] - y_data) / (cur_ylim[1] - cur_ylim[0])

        # Update limits
        event.inaxes.set_xlim([
            x_data - new_width * (1 - rel_x),
            x_data + new_width * rel_x
        ])
        event.inaxes.set_ylim([
            y_data - new_height * (1 - rel_y),
            y_data + new_height * rel_y
        ])

        # Update right axis if needed
        if event.inaxes == self.ax1:
            cur_ylim_right = self.ax2.get_ylim()
            scale = new_height / (cur_ylim[1] - cur_ylim[0])
            new_height_right = (cur_ylim_right[1] - cur_ylim_right[0]) * scale
            self.ax2.set_ylim([
                y_data - new_height_right * (1 - rel_y),
                y_data + new_height_right * rel_y
            ])

        plt.draw()

    def reset_zoom(self, event):
        """Reset zoom levels to default."""
        self.ax1.set_xlim(0.5, len(self.strikes) + 0.5)
        self.ax1.set_ylim(-0.2, 1.2)
        self.ax2.set_ylim(-0.8, 0.4)
        plt.draw()

    def compare_prices_and_slopes(self, tree, option_data, market_data):
        """Compare tree and BS prices with their slopes."""
        # Check for dividends first
        if check_dividend(market_data):
            print("Impossible de comparer avec Black-Scholes : "
                  "des dividendes ont été détectés.\n"
                  "La formule classique de Black-Scholes ne prend "
                  "pas en compte les dividendes.")
            return

        # Generate strikes
        self.strikes = [
            market_data.StartPrice + i for i in range(-11, 11)
        ]
        original_strike = option_data.strike

        # Initialize results dictionary
        results = {
            'Strike': self.strikes,
            'Prix Arbre': [],
            'Prix BS': [],
            'Arbre - BS': [],
            'Pente Arbre': [],
            'Pente BS': []
        }

        # Calculate prices for each strike
        for strike in self.strikes:
            option_data.strike = strike

            # Calculate tree price
            tree.build_tree(option_data, market_data)
            tree_price = tree.price_option(option_data, market_data)
            results['Prix Arbre'].append(tree_price)

            # Calculate BS price
            bs_price = black_scholes_price(
                market_data.StartPrice,
                strike,
                option_data.time,
                market_data.r,
                market_data.sigma,
                option_data.is_call
            )
            results['Prix BS'].append(bs_price)

            tree.release_tree_memory()

        # Calculate differences and slopes
        results['Arbre - BS'] = [
            t - b for t, b in zip(results['Prix Arbre'], results['Prix BS'])
        ]
        results['Pente Arbre'] = [None] + [
            calculate_slope(results['Prix Arbre'], self.strikes, i)
            for i in range(1, len(self.strikes))
        ]
        results['Pente BS'] = [None] + [
            calculate_slope(results['Prix BS'], self.strikes, i)
            for i in range(1, len(self.strikes))
        ]

        # Create and display DataFrame
        df = pd.DataFrame(results)
        print("\nRésultats :")
        print(df.to_string(
            float_format=lambda x: '{:.9f}'.format(x)
            if isinstance(x, float) else str(x))
        )

        # Create visualization
        self._create_visualization(results)

        # Restore original strike
        option_data.strike = original_strike

    def _create_visualization(self, results):
        """Create the visualization plot."""
        # Setup figure and axes
        fig = plt.figure(figsize=(12, 7))
        self.ax1 = plt.subplot2grid((6, 1), (0, 0), rowspan=5)
        self.ax2 = self.ax1.twinx()
        button_ax = plt.subplot2grid((6, 1), (5, 0))

        # Plot data
        x_range = range(1, len(self.strikes) + 1)
        line1 = self.ax1.plot(x_range, results['Arbre - BS'],
                             'darkgreen', label='Différence Arbre - BS',
                             linewidth=2)
        line2 = self.ax2.plot(x_range, results['Pente Arbre'],
                             'skyblue', label='Pente Arbre',
                             linewidth=2)
        line3 = self.ax2.plot(x_range, results['Pente BS'],
                             'purple', label='Pente BS',
                             linewidth=2)

        # Configure axes
        self.ax1.set_xlabel("Index du Prix d'Exercise")
        self.ax1.set_ylabel('Différence de Prix')
        self.ax2.set_ylabel('Pente')
        self.ax1.grid(True, alpha=0.3)
        self.ax1.set_xlim(0.5, len(self.strikes) + 0.5)
        self.ax1.set_ylim(-0.2, 1.2)
        self.ax2.set_ylim(-0.8, 0.4)

        # Add legend
        lines = line1 + line2 + line3
        labels = [l.get_label() for l in lines]
        self.ax1.legend(lines, labels, loc='upper left')

        # Configure title and axes
        plt.suptitle("Comparaison Arbre vs Black-Scholes en fonction du strike")
        self.ax1.set_xticks(x_range)

        # Add reset button and scroll listener
        reset_button = Button(button_ax, 'Réinitialiser Zoom')
        reset_button.on_clicked(self.reset_zoom)
        fig.canvas.mpl_connect('scroll_event', self.on_scroll)

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    from main import tree, option_data, market_data

    visualizer = PriceComparisonVisualizer()
    visualizer.compare_prices_and_slopes(tree, option_data, market_data)