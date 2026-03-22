class Pricer:
    def __init__(self, root, option, market):
        """
        Initializes the pricer with the option's root node, option parameters, and market data.

        Args:
            root: The root node for the option's tree structure.
            option: The option object containing option parameters.
            market: The market object containing market parameters.
        """
        self.root = root
        self.option = option
        self.market = market

    def price(self):
        """
        Calculates the option price through backward propagation.

        Returns:
            float: The calculated option price at the root node.
        """
        # 1. Obtain the last trunk node
        last_node_trunk = self.root.get_last_trunk_node()
        sign = 1 if self.option.is_call else -1

        # 2. Calculate terminal values
        current = last_node_trunk
        self.calculate_terminal_values(current, sign)

        # Process nodes in the upward direction
        current = last_node_trunk.up
        while current is not None:
            self.calculate_terminal_values(current, sign)
            current = current.up

        # Process nodes in the downward direction
        current = last_node_trunk.down
        while current is not None:
            self.calculate_terminal_values(current, sign)
            current = current.down

        # 3. Perform backward propagation to calculate option values
        current_trunk = last_node_trunk.parent
        while current_trunk is not None:
            # Calculate the trunk node's price
            self.calculate_node_value(current_trunk, sign)

            # Calculate prices for nodes in the upward direction
            current = current_trunk.up
            while current is not None:
                self.calculate_node_value(current, sign)
                current = current.up

            # Calculate prices for nodes in the downward direction
            current = current_trunk.down
            while current is not None:
                self.calculate_node_value(current, sign)
                current = current.down

            # Move up to the next trunk node
            current_trunk = current_trunk.parent

        return self.root.value

    def calculate_terminal_values(self, node, sign):
        """
        Calculates the terminal values for leaf nodes in the tree.

        Args:
            node: The node for which the terminal value is calculated.
            sign (int): 1 for a call option, -1 for a put option.
        """
        node.value = max(0, sign * (node.underlying - self.option.strike))
        node.is_value_available = True

    def calculate_node_value(self, node, sign):
        """
        Calculates the value of a node through backward propagation.

        Args:
            node: The node whose value is being calculated.
            sign (int): 1 for a call option, -1 for a put option.
        """
        # Expected value based on probabilities and future node values
        expected_value = (
                node.p_up * node.future_up.value +
                node.p_mid * node.future_mid.value +
                node.p_down * node.future_down.value
        )

        # Discount the expected value to present value using the market's discount factor
        node.value = expected_value * self.market.df

        # For American options, check if early exercise is optimal
        if self.option.is_american:
            intrinsic_value = max(0, sign * (node.underlying - self.option.strike))
            node.value = max(node.value, intrinsic_value)

        node.is_value_available = True
