# ip_model.py

import pandas as pd
import pulp
from csv_file_parser import parse_input_file

def ip_solve(items, W_cabin, V_cabin, W_checkin, V_checkin, risk_limit, alpha):
    """
    Solves the multi-bag packing problem using integer programming.

    Parameters:
      items (DataFrame): A pandas DataFrame with the following columns:
                         - Weight: the weight of the item.
                         - Volume: the volume of the item.
                         - MoversCost: the baseline cost to ship the item via movers.
                         - ResidualValue: the current (depreciated) monetary value of the item.
                         - SafeCabin: binary indicator (0/1) if the item is allowed in cabin baggage.
                         - SafeCheckin: binary indicator (0/1) if the item is allowed in check-in baggage.
                         - SafeMovers: binary indicator (0/1) if the item is allowed to be shipped by movers.
      W_cabin (float): Maximum weight capacity for cabin (hand baggage).
      V_cabin (float): Maximum volume capacity for cabin (hand baggage).
      W_checkin (float): Maximum weight capacity for check-in.
      V_checkin (float): Maximum volume capacity for check-in.
      risk_limit (float): Maximum total residual value allowed to be shipped via movers.
      alpha (float): Penalty factor applied to the residual value when an item is shipped.
                     This factor increases the cost of shipping high-value items.

    """
    
    # Number of items.
    n = len(items)
    
    # Convert DataFrame columns to lists for faster access.
    weights = items['Weight'].tolist()
    volumes = items['Volume'].tolist()
    movers_cost = items['MoversCost'].tolist()
    residual_value = items['ResidualValue'].tolist()
    safe_cabin = items['SafeCabin'].tolist()
    safe_checkin = items['SafeCheckin'].tolist()
    safe_movers = items['SafeMovers'].tolist()

    # Define the LP problem. We aim to minimize the total shipping cost.
    prob = pulp.LpProblem("MultiBagPacking", pulp.LpMinimize)

    # Create decision variables for each item.
    # For each item, we create three binary variables:
    # x_C[i] = 1 if item i goes into the cabin,
    # x_K[i] = 1 if item i goes into check-in,
    # x_M[i] = 1 if item i is shipped via movers.
    x_C = [pulp.LpVariable(f"x_{i}_C", cat='Binary') for i in range(n)]
    x_K = [pulp.LpVariable(f"x_{i}_K", cat='Binary') for i in range(n)]
    x_M = [pulp.LpVariable(f"x_{i}_M", cat='Binary') for i in range(n)]

    # Objective Function:
    # Only items shipped via movers incur a cost.
    # For each item i assigned to movers, the cost is:
    #   movers_cost[i] + alpha * residual_value[i].
    # Items assigned to cabin or check-in add no extra shipping cost.
    prob += pulp.lpSum((movers_cost[i] + alpha * residual_value[i]) * x_M[i] for i in range(n))
    
    # Assignment Constraint:
    # Every item must be assigned exactly one of the three modes.
    for i in range(n):
        prob += x_C[i] + x_K[i] + x_M[i] == 1, f"Assignment_{i}"

    # Capacity Constraints for Cabin:
    # The total weight and volume of items assigned to cabin must not exceed the cabin limits.
    prob += pulp.lpSum(weights[i] * x_C[i] for i in range(n)) <= W_cabin, "CabinWeight"
    prob += pulp.lpSum(volumes[i] * x_C[i] for i in range(n)) <= V_cabin, "CabinVolume"

    # Capacity Constraints for Check-in:
    # The total weight and volume of items assigned to check-in must not exceed the check-in limits.
    prob += pulp.lpSum(weights[i] * x_K[i] for i in range(n)) <= W_checkin, "CheckinWeight"
    prob += pulp.lpSum(volumes[i] * x_K[i] for i in range(n)) <= V_checkin, "CheckinVolume"

    # Compatibility Constraints:
    # Ensure that an item is only assigned to a mode if it is allowed to be placed there.
    for i in range(n):
        prob += x_C[i] <= safe_cabin[i], f"SafeCabin_{i}"
        prob += x_K[i] <= safe_checkin[i], f"SafeCheckin_{i}"
        prob += x_M[i] <= safe_movers[i], f"SafeMovers_{i}"

    # Risk-Limit Constraint:
    # The total residual value of items shipped via movers must not exceed risk_limit.
    prob += pulp.lpSum(residual_value[i] * x_M[i] for i in range(n)) <= risk_limit, "RiskLimit"

    # Solve the problem.
    prob.solve()

    # Capture the status (e.g., "Optimal", "Infeasible", etc.)
    status = pulp.LpStatus[prob.status]
    # Retrieve the minimized total cost.
    total_cost = pulp.value(prob.objective)
    
    # Build the assignment list.
    assignment = []
    for i in range(n):
        # Check the value of each binary variable for the item.
        if pulp.value(x_C[i]) == 1:
            assignment.append("Cabin")
        elif pulp.value(x_K[i]) == 1:
            assignment.append("Checkin")
        elif pulp.value(x_M[i]) == 1:
            assignment.append("Movers")
        else:
            assignment.append("Unassigned")
    
    return status, total_cost, assignment

if __name__ == "__main__":
    file_name = "uploaded_Indian_College_Student_Dorm_Items_Expanded (1).xlsx"
    print("Reading and parsing input file:", file_name)
    try:
        items = parse_input_file(file_name, "excel", movers_cost_rate=2.5)
        print(items)
        print("File parsed successfully.")
    except Exception as e:
        print("Error reading or parsing file:", e)
        exit(1)
    
    # Updated default parameters.
    W_cabin    = 7.0    # Cabin (hand baggage) weight capacity in kg.
    V_cabin    = 34.0   # Cabin (hand baggage) volume capacity in liters.
    W_checkin  = 23.0   # Check-in weight capacity in kg.
    V_checkin  = 95.5   # Check-in volume capacity in liters.
    risk_limit = 50000.0 
    alpha      = 0.2
    
    status, total_cost, assignment = ip_solve(items, W_cabin, V_cabin, W_checkin, V_checkin, risk_limit, alpha)
    print("\n=== Integer Programming Model Result ===")
    print("Status:", status)
    print("Total Cost:", total_cost)
    for i, mode in enumerate(assignment):
        print(f"Item {i}: {mode}")
