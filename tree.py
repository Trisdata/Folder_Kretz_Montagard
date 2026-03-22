from typing import List, Optional
from LatticeNode import Node
from Market import Mk
from Option import Opt
import math


class Tree:
    """
    A trinomial tree implementation for option pricing.

    This class implements a recombining trinomial lattice for pricing options,
    supporting both European and American-style derivatives with discrete dividends.

    Attributes:
        nbsteps (int): Number of time steps in the tree
        delta_t (float): Time step size
        alpha (float): Node spacing parameter
        root (Node): Root node of the tree
        nodes_by_level (List[List[Node]]): Nodes organized by tree level
        terminal_nodes (List[Node]): List of terminal nodes
    """

    def __init__(self, nbsteps: int, delta_t: float) -> None:
        """
        Initialize a new trinomial tree.

        Args:
            nbsteps: Number of time steps
            delta_t: Time step size in years
        """
        self.alpha: Optional[float] = None
        self.root: Optional[Node] = None
        self.nbsteps: int = nbsteps
        self.delta_t: float = delta_t
        self.nodes_by_level: List[List[Node]] = []
        self.terminal_nodes: List[Node] = []

    def compute_df(self, market: Mk, option: Opt) -> float:
        """
        Compute the discount factor for one time step.

        Args:
            market: Market data containing rates
            option: Option data containing maturity date

        Returns:
            float: Discount factor for one time step
        """
        time_to_maturity = option.compute_time(market.start_date)
        return math.exp(-market.r * (time_to_maturity / self.nbsteps))

    def compute_alpha(self, market: Mk) -> None:
        """
        Compute the alpha parameter that determines node spacing.

        Uses the formula: alpha = 1 + sqrt(3 * (exp(sigma^2 * dt) - 1)) * exp(r * dt)

        Args:
            market: Market data containing volatility and rate

        Raises:
            ValueError: If computed alpha is less than or equal to 1
        """
        variance_term = math.exp(market.sigma ** 2 * self.delta_t) - 1
        self.alpha = 1 + math.sqrt(3 * variance_term) * math.exp(market.r * self.delta_t)

        if self.alpha <= 1:
            raise ValueError(f"Invalid alpha value: {self.alpha}")

    def build_tree_links(self, trunk_node: Node, option:Opt, market: Mk,
                         current_step: int) -> None:
        """
        Build connections between nodes at a given tree level.

        Args:
            trunk_node: Central node at the current level
            option: Option parameters
            market: Market data
            current_step: Current time step index
        """
        # Establish trunk node connections
        trunk_node.establish_connections(market, option, self, True, False, current_step)
        current_level = [trunk_node]

        # Build upward connections
        upward_node = trunk_node.up
        while upward_node is not None:
            upward_node.establish_connections(market, option, self, False, True, current_step)
            current_level.append(upward_node)
            upward_node = upward_node.up

        # Build downward connections
        downward_node = trunk_node.down
        while downward_node is not None:
            downward_node.establish_connections(market, option, self, False, False, current_step)
            current_level.append(downward_node)
            downward_node = downward_node.down

        # Store sorted current level
        self.nodes_by_level.append(sorted(current_level, key=lambda x: x.underlying))

    def build_tree(self, option: Opt, market: Mk) -> None:
        """
        Build the complete trinomial tree.

        Args:
            option: Option parameters
            market: Market data

        Raises:
            Exception: If trunk node initialization fails
        """
        # Initialize root
        self.root = Node(market.StartPrice)
        self.nodes_by_level = [[self.root]]
        self.compute_alpha(market)

        # Build from root
        self.root.establish_connections(market, option, self, True, False, 0)
        trunk_node = self.root.future_mid

        # Build level by level
        for step in range(1, self.nbsteps):
            if trunk_node is None:
                raise Exception(f"Erreur d'initialisation du nœud tronc à l'étape {step}")

            self.build_tree_links(trunk_node, option, market, step)
            trunk_node = trunk_node.future_mid

        self.collect_terminal_nodes(trunk_node)

    def collect_terminal_nodes(self, last_trunk: Node) -> None:
        """
        Collect and sort terminal nodes of the tree.

        Args:
            last_trunk: Last central node of the tree
        """
        self.terminal_nodes = [last_trunk]

        # Collect upward nodes
        up_node = last_trunk.up
        while up_node is not None:
            self.terminal_nodes.append(up_node)
            up_node = up_node.up

        # Collect downward nodes
        down_node = last_trunk.down
        while down_node is not None:
            self.terminal_nodes.append(down_node)
            down_node = down_node.down

        self.terminal_nodes.sort(key=lambda x: x.underlying)

    def price_option(self, option: Opt, market: Mk) -> float:
        """
        Price the option using backward induction.

        Args:
            option: Option parameters containing maturity and type
            market: Market data containing rates and start date

        Returns:
            float: Option price
        """
        self._calculate_terminal_values(option)

        # Calculate discount factor using option's maturity
        df = math.exp(-market.r * self.delta_t)
        sign = option.sign_option()

        final_value = self._backward_propagation(option, df, sign)
        return final_value

    def _calculate_terminal_values(self, option: Opt) -> None:
        """
        Calculate terminal values for all leaf nodes.

        Args:
            option: Option parameters
        """
        for node in self.terminal_nodes:
            node.value = max(0, option.sign_option() * (node.underlying - option.strike))
            node.is_value_available = True

    def _backward_propagation(self, option: Opt, df: float, sign: int) -> float:
        """
        Perform backward propagation to calculate option values.

        Args:
            option: Option parameters
            df: Discount factor
            sign: Option type indicator from option.sign_option()

        Returns:
            float: Option value at root node
        """
        for level_idx in range(len(self.nodes_by_level) - 1, -1, -1):
            for node in self.nodes_by_level[level_idx]:
                if not hasattr(node, 'future_mid') or node.future_mid is None:
                    continue

                self._process_node(node, option, df, sign)

        return self.root.value

    def _process_node(self, node: Node, option: Opt, df: float, sign: int) -> None:
        """
        Process a single node during backward propagation.

        Args:
            node: Current node to process
            option: Option parameters
            df: Discount factor
            sign: Option type indicator
        """
        expected_value = (node.p_up * node.future_up.value +
                          node.p_mid * node.future_mid.value +
                          node.p_down * node.future_down.value) * df


        node.value = expected_value

        node.is_value_available = True

    def get_last_trunk_node(self) -> Node:
        """
        Get the last central node of the tree.

        Returns:
            Node: Last central node
        """
        current_node = self.root
        while current_node.future_mid is not None:
            current_node = current_node.future_mid
        return current_node

    def release_tree_memory(self) -> None:
        """
        Clean up tree memory by removing all node references.
        """
        for level in self.nodes_by_level:
            for node in level:
                node.future_up = None
                node.future_down = None
                node.future_mid = None
                node.parent = None
                node.up = None
                node.down = None

        self.nodes_by_level = []
        self.terminal_nodes = []
        self.root = None