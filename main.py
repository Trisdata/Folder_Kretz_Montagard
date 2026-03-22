import time
import math
from Option import Opt
from Market import Mk
from tree import Tree
from A_main_Pricer import Pricer

# Start timer for total execution time
start_total = time.time()

# Create an option instance
option_data = Opt(
    strike=101,
    maturity_date='2024-12-26',
    is_american=False,
    is_call=True
)

# Create a market instance
market_data = Mk(
    interest_rate=0.06,
    volatility=0.21,
    dividend=3,
    start_price=100,
    start_date='2024-03-01',
    div_date='2024-06-02'
)

# Calculate time to maturity in years
time_to_maturity = option_data.compute_time(market_data.start_date)

# Define the number of steps and compute the delta_t for the tree
nb_steps = 100
delta_t = time_to_maturity / nb_steps

# Create the tree instance
tree = Tree(nb_steps, delta_t)

# Calculate the discount factor and add it to market data
market_data.df = math.exp(-market_data.r * delta_t)

# Measure tree construction time
start_build = time.time()
tree.build_tree(option_data, market_data)
build_time = time.time() - start_build
print(f"\nTree building time: {build_time:.2f} seconds")

# Measure pricing time
start_price = time.time()
pricer = Pricer(root=tree.root, option=option_data, market=market_data)
option_price = pricer.price()
price_time = time.time() - start_price

# Display results
print(f"Pricing time: {price_time:.2f} seconds")
print(f"Calculated Option Price: {option_price:.4f}")

# Total execution time
total_time = time.time() - start_total
print(f"\nTotal execution time: {total_time:.2f} seconds")

'''Il faut noter que le cache ne se cache pas et prend du temps, 
mais le vider artificiellement nous empêcherait de créer les plots'''
