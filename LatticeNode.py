import math

class Node:
    """Class representing a node in the trinomial tree for option pricing."""

    def __init__(self, underlying_price, tree=None, parent=None):
        """Initialize a node with underlying price, tree reference, and parent node."""
        self.underlying = underlying_price  # Underlying asset price at this node
        self.tree = tree  # Reference to the associated tree
        self.parent = parent  # Reference to the parent node

        # Future nodes for tree traversal
        self.future_mid = None
        self.future_up = None
        self.future_down = None

        # Current level connections
        self.up = None
        self.down = None

        # Transition probabilities
        self.p_up = 0.0
        self.p_mid = 0.0
        self.p_down = 0.0

        # Pricing information
        self.is_value_available = False  # Flag indicating if value is available
        self.value = 0.0  # Calculated value of the node

    def calculate_forward_price(self, market_data, option_data, current_step, tree_data):
        """
        Calculate the forward price with dividend adjustment.

        Args:
            market_data: Market data object containing financial parameters.
            option_data: Option data object with option specifications.
            current_step: Current time step in the tree.
            tree_data: Data containing tree configuration.

        Returns:
            Calculated forward price.
        """
        forward = self.underlying * math.exp(market_data.r * tree_data.delta_t)

        # Adjust forward price for dividends if applicable
        if hasattr(market_data, 'D') and market_data.D != 0:
            time_to_dividend = (market_data.div_date - market_data.start_date).days / 365.0
            steps_to_dividend = time_to_dividend / tree_data.delta_t
            current_time = current_step * tree_data.delta_t
            dividend_time = steps_to_dividend * tree_data.delta_t

            if current_time <= dividend_time < (current_time + tree_data.delta_t):
                forward = (self.underlying - market_data.D) * math.exp(market_data.r * tree_data.delta_t)

        return forward

    def calculate_transition_probabilities(self, option_data, market_data, tree, current_step):
        """
        Calculate transition probabilities using VBA method with system constraints.

        Args:
            option_data: Option data for probability calculation.
            market_data: Market data containing financial parameters.
            tree: Reference to the tree for node connections.
            current_step: Current time step in the tree.
        """
        # Calculate variance and expected value
        variance = (self.underlying ** 2) * math.exp(2 * market_data.r * tree.delta_t) * \
                   (math.exp(market_data.sigma ** 2 * tree.delta_t) - 1)

        expected_value = self.calculate_forward_price(market_data, option_data, current_step, tree)

        # Exact formula for p_down based on the system of equations
        term1 = (self.future_mid.underlying ** -2) * (variance + expected_value ** 2) - 1
        term2 = (tree.alpha + 1) * ((self.future_mid.underlying ** -1) * expected_value - 1)
        denom = (1 - tree.alpha) * (tree.alpha ** -2 - 1)

        self.p_down = (term1 - term2) / denom

        # Calculate p_up based on the expected value equation
        self.p_up = (((1 / self.future_mid.underlying) * expected_value - 1) -
                     (1 / tree.alpha - 1) * self.p_down) / (tree.alpha - 1)

        # p_mid completes to 1
        self.p_mid = 1 - self.p_up - self.p_down

    def establish_connections(self, market_data, option_data, tree, is_mid_node, is_upward, step):
        """
        Establish connections between nodes.

        Args:
            market_data: Market data for node connection establishment.
            option_data: Option data for pricing calculations.
            tree: Reference to the tree.
            is_mid_node: Boolean indicating if the current node is a mid node.
            is_upward: Boolean indicating if the connection is upward.
            step: Current step in the tree.
        """
        if is_mid_node:
            self.create_mid_links(market_data, option_data, step, tree)
        else:
            self.future_mid = self.get_optimal_future_mid_node(market_data, option_data, tree, is_upward, step)

            if is_upward:
                if self.future_mid.up is None:
                    self.future_up = generate_node(self.future_mid.underlying * tree.alpha, tree)
                    self.future_mid.up = self.future_up
                    self.future_up.down = self.future_mid
                    self.future_up.parent = self
                else:
                    self.future_up = self.future_mid.up
                self.future_down = self.future_mid.down
            else:
                if self.future_mid.down is None:
                    self.future_down = generate_node(self.future_mid.underlying / tree.alpha, tree)
                    self.future_mid.down = self.future_down
                    self.future_down.up = self.future_mid
                    self.future_down.parent = self
                else:
                    self.future_down = self.future_mid.down
                self.future_up = self.future_mid.up

        self.calculate_transition_probabilities(option_data, market_data, tree, step)

    def create_mid_links(self, market_data, option_data, current_step, tree):
        """
        Create links for a mid node.

        Args:
            market_data: Market data for calculations.
            option_data: Option data for pricing.
            current_step: Current time step in the tree.
            tree: Reference to the tree.
        """
        forward = self.calculate_forward_price(market_data, option_data, current_step, tree)

        self.future_mid = generate_node(forward, tree)
        self.future_up = generate_node(forward * tree.alpha, tree)
        self.future_down = generate_node(forward / tree.alpha, tree)

        # Establish connections between the mid and future nodes
        self.future_mid.up = self.future_up
        self.future_mid.down = self.future_down
        self.future_down.up = self.future_mid
        self.future_up.down = self.future_mid

        # Set parent-child relationships
        self.future_mid.parent = self
        self.future_up.parent = self.future_mid
        self.future_down.parent = self.future_mid

    def get_optimal_future_mid_node(self, market_data, option_data, tree, is_upward, current_step):
        """
        Find the optimal future mid node.

        Args:
            market_data: Market data for calculations.
            option_data: Option data for pricing.
            tree: Reference to the tree.
            is_upward: Boolean indicating upward direction.
            current_step: Current time step in the tree.

        Returns:
            The optimal future mid node.
        """
        if is_upward:
            candidate = self.down.future_up
        else:
            candidate = self.up.future_down

        forward = self.calculate_forward_price(market_data, option_data, current_step, tree)

        if self.is_node_optimal(candidate, market_data, option_data, current_step, tree):
            return candidate
        elif forward > candidate.underlying * (1 + (tree.alpha - 1) / 2):
            return self.find_optimal_ascending(candidate, market_data, option_data, current_step, tree)
        else:
            return self.find_optimal_descending(candidate, market_data, option_data, current_step, tree)

    def find_optimal_ascending(self, start_node, market_data, option_data, current_step, tree):
        """Perform upward search for the optimal node."""
        current = start_node
        while not self.is_node_optimal(current, market_data, option_data, current_step, tree):
            if current.up is None:
                new_node = generate_node(current.underlying * tree.alpha, tree)
                new_node.down = current
                current.up = new_node
                new_node.parent = current
                return new_node
            current = current.up
        return current

    def find_optimal_descending(self, start_node, market_data, option_data, current_step, tree):
        """Perform downward search for the optimal node."""
        current = start_node
        while not self.is_node_optimal(current, market_data, option_data, current_step, tree):
            if current.down is None:
                new_node = generate_node(current.underlying / tree.alpha, tree)
                new_node.up = current
                current.down = new_node
                new_node.parent = current
                return new_node
            current = current.down
        return current

    def is_node_optimal(self, node, market_data, option_data, current_step, tree):
        """Check if the node is optimal based on forward price bounds."""
        forward = self.calculate_forward_price(market_data, option_data, current_step, tree)
        upper_bound = node.underlying * (1 + (tree.alpha - 1) / 2)
        lower_bound = node.underlying * (1 - (tree.alpha - 1) / (2 * tree.alpha))
        return lower_bound <= forward <= upper_bound

    def get_last_trunk_node(self):
        """
        Obtain the last trunk node by following future_mid links.

        Returns:
            The last node in the trunk.
        """
        current_node = self
        while current_node.future_mid is not None:
            current_node = current_node.future_mid
        return current_node


def generate_node(underlying, tree):
    """Generate a new node with the specified underlying price."""
    new_node = Node(underlying)
    new_node.underlying = underlying
    new_node.tree = tree
    return new_node
