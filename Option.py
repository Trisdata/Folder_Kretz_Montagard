import datetime as dt


class Opt:
    def __init__(self, strike: float, maturity_date: str, is_american: bool, is_call: bool):
        """
        Initializes an option with given parameters.

        Args:
            strike (float): Strike price (e.g., 104)
            maturity_date (str): Maturity date in 'YYYY-MM-DD' format
            is_american (bool): True if American option, False if European
            is_call (bool): True if call option, False if put
        """
        self.strike: float = strike
        self.maturity_date: dt.date = dt.datetime.strptime(maturity_date, '%Y-%m-%d').date()
        self.is_american: bool = is_american
        self.is_call: bool = is_call
        self.time: float = 0.0  # Will be calculated later

    def compute_time(self, start_date) -> float:
        """
        Calculates the time to maturity in years.

        Args:
            start_date (str or datetime.date): Can be a date string in 'YYYY-MM-DD' format
                                               or a datetime.date object.

        Returns:
            float: Time to maturity in years.
        """
        if isinstance(start_date, str):
            start_date = dt.datetime.strptime(start_date, '%Y-%m-%d').date()

        # Calculate the number of days until maturity and convert to years
        days_until_maturity = (self.maturity_date - start_date).days
        self.time = days_until_maturity / 365.0
        return self.time

    def sign_option(self) -> int:
        """
        Determines the sign of the option based on its type.

        Returns:
            int: 1 for a call option and -1 for a put option.
        """
        return 1 if self.is_call else -1
