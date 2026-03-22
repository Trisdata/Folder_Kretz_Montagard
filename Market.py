import datetime as dt


class Mk:
    def __init__(self, interest_rate: float, volatility: float, dividend: float,
                 start_price: float, start_date: str, div_date: str):
        """
        Initializes market data with relevant parameters.

        Args:
            interest_rate (float): Risk-free interest rate.
            volatility (float): Market volatility (sigma).
            dividend (float): Dividend yield (D).
            start_price (float): Starting price of the asset.
            start_date (str): Start date in 'YYYY-MM-DD' format.
            div_date (str): Date of the dividend payment in 'YYYY-MM-DD' format.
        """
        self.r: float = interest_rate          # Interest rate
        self.sigma: float = volatility          # Volatility
        self.D: float = dividend                # Dividend yield
        self.StartPrice: float = start_price    # Initial price of the asset

        # Convert start_date and div_date from strings to datetime.date objects
        self.start_date: dt.date = dt.datetime.strptime(start_date, '%Y-%m-%d').date()
        self.div_date: dt.date = dt.datetime.strptime(div_date, '%Y-%m-%d').date()
