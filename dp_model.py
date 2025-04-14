# dp_model.py

import pandas as pd
import math
import functools
from csv_file_parser import parse_input_file  # Import our custom file parser

INF = float('inf')

def dp_solve(items, W_cabin, V_cabin, W_checkin, V_checkin, risk_limit, alpha):
    """
    Solves the multi-bag packing problem using dynamic programming.
    :param items: DataFrame with columns: Weight, Volume, MoversCost, ResidualValue, SafeCabin, SafeCheckin, SafeMovers
    :param W_cabin: Maximum weight capacity for cabin (hand baggage).
    :param V_cabin: Maximum volume capacity for cabin (hand baggage).
    :param W_checkin: Maximum weight capacity for check-in.
    :param V_checkin: Maximum volume capacity for check-in.
    :param risk_limit: Maximum total residual value allowed for movers.
    :param alpha: Penalty factor for shipping via movers.
    :return: Total cost and assignment list per item.
    """
    n = len(items)
    weights = items['Weight'].tolist()
    volumes = items['Volume'].tolist()
    movers_cost = items['MoversCost'].tolist()
    residual_value = items['ResidualValue'].tolist()
    safe_cabin = items['SafeCabin'].tolist()
    safe_checkin = items['SafeCheckin'].tolist()
    safe_movers = items['SafeMovers'].tolist()

     # Use lru_cache to memoize the results of the dp() function. This avoids redundant recalculations
    # by caching the output for each unique state (i, wc, vc, wk, vk, r). With maxsize=None, the cache 
    # can grow without bound, which is acceptable if the total number of distinct states is manageable.
    @functools.lru_cache(maxsize=None)
    def dp(i, wc, vc, wk, vk, r):
        # Base case: if all items have been considered, no additional cost.
        if i == n:
            return 0, []
        
        best_cost = INF
        best_decision = None

        # Option 1: Place item i in the cabin.
        if safe_cabin[i] == 1 and (wc + weights[i] <= W_cabin) and (vc + volumes[i] <= V_cabin):
            cost_next, decision_next = dp(i + 1, wc + weights[i], vc + volumes[i], wk, vk, r)
            if cost_next < best_cost:
                best_cost = cost_next
                best_decision = [("Cabin", i)] + decision_next

        # Option 2: Place item i in the check-in.
        if safe_checkin[i] == 1 and (wk + weights[i] <= W_checkin) and (vk + volumes[i] <= V_checkin):
            cost_next, decision_next = dp(i + 1, wc, vc, wk + weights[i], vk + volumes[i], r)
            if cost_next < best_cost:
                best_cost = cost_next
                best_decision = [("Checkin", i)] + decision_next

        # Option 3: Ship item i via movers.
        # Check if shipping this item would exceed the risk limit.
        if safe_movers[i] == 1 and (r + residual_value[i] <= risk_limit):
            # Compute cost for shipping this item: base cost + penalty.
            cost_here = movers_cost[i] + alpha * residual_value[i]
            cost_next, decision_next = dp(i + 1, wc, vc, wk, vk, r + residual_value[i])
            total_cost = cost_here + cost_next
            if total_cost < best_cost:
                best_cost = total_cost
                best_decision = [("Movers", i)] + decision_next

        # If no valid decision was found, return INF cost.
        if best_decision is None:
            return INF, []
        return best_cost, best_decision

    # Start recursion from the first item (index 0) with empty bags and zero residual value.
    total_cost, decisions = dp(0, 0, 0, 0, 0, 0)
    
    # Build an assignment list (length n). 
    # Each entry corresponds to the final mode chosen for the corresponding item.
    assignment = ['Unassigned'] * n
    for mode, i in decisions:
        assignment[i] = mode
    return total_cost, assignment

# __main__ section for quick testing.
if __name__ == "__main__":
    # Hardcoded file name (ensure the file exists in the folder).
    file_name = "uploaded_Indian_College_Student_Dorm_Items_Expanded (1).xlsx"
    print("Reading and parsing input file:", file_name)
    try:
        # Use movers_cost_rate as a user-defined parameter 
        items = parse_input_file(file_name, "excel", movers_cost_rate=2.5)
        print(items)
        print("File parsed successfully.")
    except Exception as e:
        print("Error reading or parsing file:", e)
        exit(1)

    # Set updated default model parameters:
    # For hand (cabin) baggage: Weight = 2.2 kg, Volume = 34 liters.
    # For check-in baggage: Weight = 3.5 kg, Volume = 95.5 liters.
    W_cabin    = 7.0    # Cabin (hand baggage) weight capacity in kg.
    V_cabin    = 34.0   # Cabin (hand baggage) volume capacity in liters.
    W_checkin  = 23.0   # Check-in weight capacity in kg.
    V_checkin  = 95.5   # Check-in volume capacity in liters.
    risk_limit = 50000.0 
    alpha      = 0.2    
    
    total_cost, assignment = dp_solve(items, W_cabin, V_cabin, W_checkin, V_checkin, risk_limit, alpha)
    print("\n=== Dynamic Programming Model Result ===")
    print("Total Cost:", total_cost)
    for i, mode in enumerate(assignment):
        print(f"Item {i}: {mode}")
