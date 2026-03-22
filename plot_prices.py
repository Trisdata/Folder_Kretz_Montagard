import webbrowser
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import plotly.io as pio
import sys
from main import option_data, market_data, option_price, tree

# Add path to main.py location if needed
sys.path.append(".")

# Import variables from main
exec(open("main.py").read())


class TreeVisualizer:
    """A class to visualize option pricing trees with color gradients."""

    def __init__(self, tree, option_data, market_data, option_price):
        """Initialize the visualizer with tree and option data."""
        self.tree = tree
        self.option_data = option_data
        self.market_data = market_data
        self.option_price = option_price

        # Visualization data containers
        self.node_positions = {}
        self.x_coords = []
        self.y_coords = []
        self.values = []
        self.edge_x = []
        self.edge_y = []

    def calculate_node_positions(self):
        """Calculate node positions with vertical scaling adjustment."""
        time_steps = len(self.tree.nodes_by_level)
        x_spacing = np.linspace(0, 100, time_steps)

        # Get all underlying values for scaling
        underlying_values = [node.underlying
                             for level in self.tree.nodes_by_level
                             for node in level]

        # Scale adjustment for better visualization
        min_value = min(underlying_values)
        max_value = max(underlying_values)
        value_range = max_value - min_value
        padding = value_range * 0.2
        adjusted_min = min_value - padding
        adjusted_max = max_value + padding
        adjusted_range = adjusted_max - adjusted_min

        # Calculate positions for each node
        for level_idx, nodes in enumerate(self.tree.nodes_by_level):
            x_pos = x_spacing[level_idx]
            nodes_sorted = sorted(nodes, key=lambda n: n.underlying)

            for node in nodes_sorted:
                y_pos = ((node.underlying - adjusted_min) / adjusted_range) * 100
                self.node_positions[id(node)] = (x_pos, y_pos)
                self.x_coords.append(x_pos)
                self.y_coords.append(y_pos)
                self.values.append(node.value if hasattr(node, 'value') else 0)

    def add_edges(self):
        """Add edges between connected nodes in the tree."""
        for level_idx, nodes in enumerate(self.tree.nodes_by_level[:-1]):
            for node in nodes:
                current_pos = self.node_positions[id(node)]

                # Add connections for all future nodes
                for future_attr in ['future_up', 'future_mid', 'future_down']:
                    future_node = getattr(node, future_attr, None)
                    if future_node:
                        future_pos = self.node_positions[id(future_node)]
                        self.edge_x.extend([current_pos[0], future_pos[0], None])
                        self.edge_y.extend([current_pos[1], future_pos[1], None])

    def get_color(self, value, min_value, max_value):
        """Generate a color on a red-green gradient based on value position."""
        if max_value == min_value:
            normalized = 0.5
        else:
            normalized = (value - min_value) / (max_value - min_value)

        # Red to green gradient
        red = int(255 * (1 - normalized))
        green = int(255 * normalized)

        return f'rgba({red}, {green}, 0, 0.7)'

    def create_figure(self):
        """Create the plotly figure with nodes and edges."""
        fig = make_subplots(rows=1, cols=1)

        # Add edge traces
        fig.add_trace(
            go.Scatter(
                x=self.edge_x,
                y=self.edge_y,
                mode='lines',
                line=dict(color='rgba(128, 128, 128, 0.2)', width=1),
                hoverinfo='none',
                showlegend=False
            )
        )

        # Calculate color gradient values
        min_value = min(self.values)
        max_value = max(self.values)
        colors = [self.get_color(v, min_value, max_value) for v in self.values]

        # Add node traces
        nodes = [n for level in self.tree.nodes_by_level for n in level]
        fig.add_trace(
            go.Scatter(
                x=self.x_coords,
                y=self.y_coords,
                mode='markers+text',
                marker=dict(
                    size=10,
                    color=colors,
                    line=dict(width=1, color='black')
                ),
                text=[f"{v:.2f}" for v in self.values],
                textposition="bottom center",
                hovertext=[f"Underlying: {node.underlying:.2f}<br>Option: {v:.2f}"
                           for node, v in zip(nodes, self.values)],
                hoverinfo='text',
                name='Nodes'
            )
        )

        # Calculate zoom ranges
        x_min, x_max = min(self.x_coords), max(self.x_coords)
        y_min, y_max = min(self.y_coords), max(self.y_coords)
        x_padding = (x_max - x_min) * 0.1
        y_padding = (y_max - y_min) * 0.2
        x_range = [x_min - x_padding, x_max + x_padding]
        y_range = [y_min - y_padding, y_max + y_padding]

        # Update layout with title and axes
        fig.update_layout(
            title=dict(
                text=(f"{'Call' if self.option_data.is_call else 'Put'} "
                      f"{'American' if self.option_data.is_american else 'European'}<br>"
                      f"Strike = {self.option_data.strike:.2f}, Price = {self.option_price:.4f}"),
                x=0.5,
                y=0.95
            ),
            showlegend=False,
            hovermode='closest',
            width=1200,
            height=800,
            xaxis=dict(title='Time', range=x_range, showgrid=True),
            yaxis=dict(title='Underlying Price', range=y_range, showgrid=True),
            updatemenus=[dict(
                type="buttons",
                direction="left",
                buttons=[dict(
                    args=[{"xaxis.range": x_range, "yaxis.range": y_range}],
                    label="Reset Zoom",
                    method="relayout"
                )],
                x=0.1,
                y=1.1
            )]
        )

        # Add color legend
        self._add_color_legend(fig, min_value, max_value)

        return fig

    def _add_color_legend(self, fig, min_value, max_value):
        """Add color gradient legend to the figure."""
        fig.add_annotation(
            x=1.05, y=0.9,
            xref="paper", yref="paper",
            text="Option Value",
            showarrow=False
        )

        for label, value, y_pos in [
            ("Max", max_value, 0.85),
            ("Min", min_value, 0.8)
        ]:
            fig.add_annotation(
                x=1.05, y=y_pos,
                xref="paper", yref="paper",
                text=f"{label}: {value:.2f}",
                showarrow=False,
                bgcolor=self.get_color(value, min_value, max_value),
                bordercolor="black",
                borderwidth=1
            )

    def visualize(self):
        """Main visualization method that generates and displays the tree."""
        print("Generating visualization...")
        self.calculate_node_positions()
        self.add_edges()
        fig = self.create_figure()

        # Save and display the visualization
        temp_path = "tree_visualization.html"
        fig.write_html(temp_path)
        abs_path = os.path.abspath(temp_path)
        file_url = f"file:///{abs_path.replace(os.sep, '/')}"

        try:
            webbrowser.open(file_url)
        except Exception as e:
            print(f"Please open manually: {abs_path}")

        return fig


def main():
    """Main execution function that handles the visualization process."""
    # Set plotly renderer
    pio.renderers.default = "browser"


    # Create and display visualization
    visualizer = TreeVisualizer(tree, option_data, market_data, option_price)
    fig = visualizer.visualize()

    return fig


if __name__ == "__main__":
    main()
