import plotly.graph_objects as go
import numpy as np
import webbrowser
import os
import time
import sys

# Add the path to main.py if needed
sys.path.append(".")

# Import variables from main.py
from main import option_data, tree, option_price


class ProbabilityVisualizer:
    """Visualizer for probabilities in a trinomial tree with pruning."""

    def __init__(self, tree, pruning_threshold):
        """Initialize the visualizer with tree and pruning threshold."""
        self.tree = tree
        self.pruning_threshold = pruning_threshold
        self.node_positions = {}
        self.x_coords = []
        self.y_coords = []
        self.probabilities = []
        self.edge_x = []
        self.edge_y = []
        self.node_probabilities = {}
        self.pruned_nodes = set()  # Set of pruned nodes

    def calculate_probabilities(self):
        """Calculate probabilities for each node in the tree."""
        # Initialize the root with probability 1
        self.node_probabilities[self.tree.root] = 1.0

        # Traverse the tree level by level
        current_trunk = self.tree.root
        while current_trunk is not None and hasattr(current_trunk, 'future_mid'):
            self._propagate_probabilities(current_trunk)

            current_up = current_trunk.up
            while current_up is not None:
                self._propagate_probabilities(current_up)
                current_up = current_up.up

            current_down = current_trunk.down
            while current_down is not None:
                self._propagate_probabilities(current_down)
                current_down = current_down.down

            current_trunk = current_trunk.future_mid

        # Apply pruning after calculating probabilities
        self._apply_pruning()

    def _propagate_probabilities(self, node):
        """Propagate probabilities from a node to its successors."""
        if node not in self.node_probabilities:
            return

        current_prob = self.node_probabilities[node]

        # Update probabilities for future nodes, summing probabilities from multiple paths
        if hasattr(node, 'future_up') and node.future_up is not None:
            next_prob = current_prob * node.p_up
            self.node_probabilities[node.future_up] = \
                self.node_probabilities.get(node.future_up, 0) + next_prob

        if hasattr(node, 'future_mid') and node.future_mid is not None:
            next_prob = current_prob * node.p_mid
            self.node_probabilities[node.future_mid] = \
                self.node_probabilities.get(node.future_mid, 0) + next_prob

        if hasattr(node, 'future_down') and node.future_down is not None:
            next_prob = current_prob * node.p_down
            self.node_probabilities[node.future_down] = \
                self.node_probabilities.get(node.future_down, 0) + next_prob

    def _apply_pruning(self):
        """Identify nodes to be pruned based on the pruning threshold."""
        for level in self.tree.nodes_by_level[1:]:  # Skip the root level
            for node in level:
                if node in self.node_probabilities and self.node_probabilities[node] < self.pruning_threshold:
                    self.pruned_nodes.add(node)

    def calculate_node_positions(self):
        """Calculate positions for nodes with vertical scaling adjustment."""
        time_steps = len(self.tree.nodes_by_level)
        x_spacing = np.linspace(0, 100, time_steps)

        # Get underlying values for scaling (only non-pruned nodes)
        underlying_values = []
        for level in self.tree.nodes_by_level:
            for node in level:
                if node not in self.pruned_nodes:
                    underlying_values.append(node.underlying)

        if not underlying_values:  # If all nodes are pruned
            print("Warning: All nodes have been pruned!")
            return

        # Scale adjustment for better visualization
        min_value = min(underlying_values)
        max_value = max(underlying_values)
        value_range = max_value - min_value
        padding = value_range * 0.2
        adjusted_min = min_value - padding
        adjusted_max = max_value + padding
        adjusted_range = adjusted_max - adjusted_min

        # Calculate positions for each non-pruned node
        for level_idx, nodes in enumerate(self.tree.nodes_by_level):
            x_pos = x_spacing[level_idx]
            nodes_sorted = sorted(nodes, key=lambda n: n.underlying)

            for node in nodes_sorted:
                if node not in self.pruned_nodes:
                    y_pos = ((node.underlying - adjusted_min) / adjusted_range) * 100
                    self.node_positions[id(node)] = (x_pos, y_pos)
                    self.x_coords.append(x_pos)
                    self.y_coords.append(y_pos)
                    self.probabilities.append(self.node_probabilities.get(node, 0))

    def add_edges(self):
        """Add edges between non-pruned nodes."""
        for level_idx, nodes in enumerate(self.tree.nodes_by_level[:-1]):
            for node in nodes:
                if node in self.pruned_nodes:
                    continue

                if id(node) not in self.node_positions:
                    continue

                current_pos = self.node_positions[id(node)]

                for future_attr in ['future_up', 'future_mid', 'future_down']:
                    future_node = getattr(node, future_attr, None)
                    if future_node and future_node not in self.pruned_nodes:
                        if id(future_node) in self.node_positions:
                            future_pos = self.node_positions[id(future_node)]
                            self.edge_x.extend([current_pos[0], future_pos[0], None])
                            self.edge_y.extend([current_pos[1], future_pos[1], None])

    def create_figure(self):
        """Create the Plotly figure with nodes and edges."""
        fig = go.Figure()

        # Add edges
        if self.edge_x and self.edge_y:
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

        # Add nodes with color scale for probabilities
        if self.x_coords and self.y_coords and self.probabilities:
            nodes = [n for level in self.tree.nodes_by_level for n in level if n not in self.pruned_nodes]
            non_zero_probs = [p for p in self.probabilities if p > 0]

            fig.add_trace(
                go.Scatter(
                    x=self.x_coords,
                    y=self.y_coords,
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=self.probabilities,
                        colorscale='Viridis',
                        colorbar=dict(title='Probability'),
                        showscale=True,
                        colorbar_tickformat='.1e',
                        cmin=min(non_zero_probs) if non_zero_probs else 0,
                        cmax=max(self.probabilities) if self.probabilities else 1,
                        line=dict(width=1, color='black')
                    ),
                    hovertext=[f"Underlying: {node.underlying:.2f}<br>Probability: {prob:.2e}"
                               for node, prob in zip(nodes, self.probabilities)],
                    hoverinfo='text',
                    name='Nodes'
                )
            )

        # Update layout
        pruning_info = f"Pruning threshold: {self.pruning_threshold}"
        fig.update_layout(
            title=dict(
                text=(f"Probability Distribution - "
                      f"{'Call' if option_data.is_call else 'Put'} "
                      f"{'American' if option_data.is_american else 'European'}<br>"
                      f"Strike = {option_data.strike:.2f}, Price = {option_price:.4f}<br>"
                      f"{pruning_info}"),
                x=0.5,
                y=0.95
            ),
            showlegend=False,
            hovermode='closest',
            width=1200,
            height=800,
            xaxis=dict(title='Time Steps', showgrid=True),
            yaxis=dict(title='Underlying Price', showgrid=True)
        )

        return fig

    def visualize(self):
        """Main visualization method."""
        print("Calculating probabilities...")
        self.calculate_probabilities()

        print("Generating visualization...")
        self.calculate_node_positions()
        self.add_edges()

        print(f"Number of non-pruned nodes: {len(self.node_positions)}")
        print(f"Number of total nodes: {sum(len(level) for level in self.tree.nodes_by_level)}")

        fig = self.create_figure()

        # Save and display the visualization
        temp_path = "probability_visualization.html"
        fig.write_html(temp_path)
        abs_path = os.path.abspath(temp_path)
        file_url = f"file://{abs_path}"
        webbrowser.open(file_url)

        return fig


def main(pruning_threshold):
    """Main execution for visualization."""
    start_time = time.time()

    visualizer = ProbabilityVisualizer(tree, pruning_threshold)
    fig = visualizer.visualize()

    elapsed_time = time.time() - start_time
    print(f"Visualization completed in {elapsed_time:.2f} seconds.")


if __name__ == "__main__":
    # Pruning threshold can be adjusted as needed
    PRUNING_THRESHOLD = 1e-6
    main(PRUNING_THRESHOLD)