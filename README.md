# Multi-Bag Packing Optimization

This project implements an optimization model to help pack items into different shipping modes—specifically:
- **Cabin (Hand Baggage)**
- **Check-in Baggage**
- **Movers**

The optimization uses two solution approaches:
1. **Dynamic Programming (DP) Model** (`dp_model.py`)
   - Recursively computes an optimal assignment of items into the three modes, while keeping track of used capacities and a risk constraint.
2. **Integer Programming (IP) Model** (`ip_model.py`)
   - Formulates the problem as a Mixed-Integer Linear Program (MILP) using PuLP and finds an optimal solution.

In addition, a CSV/Excel parser (`csv_file_parser.py`) reads the input file and calculates:
- **ResidualValue**: Computed from the monetary value and depreciation.
- **MoversCost**: Determined based on the item's volume multiplied by a user-defined mover's cost rate.
- **Safety Flags**:  
  The parser determines two safety flags—**SafeCabin** and **SafeCheckin**—using the "Airline Baggage Type" field. The logic is as follows:
  - If the "Airline Baggage Type" is `"Hand Baggage"`, then **SafeCabin** is set to 1 and **SafeCheckin** is set to 0.
  - If the "Airline Baggage Type" is `"Check-in Baggage"`, then **SafeCabin** is set to 0 and **SafeCheckin** is set to 1.
  - The parser also checks the item volume; if the volume exceeds the maximum allowed for the corresponding baggage type, the safety flag is overridden to 0.
- **SafeMovers**: All items are assumed to be allowed to be shipped via movers.

A **Streamlit UI** (`app.py`) is provided to let the user choose between:
1. Uploading an Excel/CSV file
2. Entering data manually

## Project Structure

- `csv_file_parser.py`  
  Parses the input file, computes derived fields (ResidualValue and MoversCost), and determines safety flags using simple logic based on the "Airline Baggage Type" field and volume limits.
  
- `dp_model.py`  
  Implements the Dynamic Programming model. It uses recursion with memoization (via `functools.lru_cache`) to determine the optimal assignment of items to modes, considering capacity constraints and a risk limit.
  
- `ip_model.py`  
  Implements the Integer Programming model using PuLP. It creates binary decision variables for assigning items and minimizes the total shipping cost (which is incurred only for items shipped via movers, along with a penalty factor `alpha` multiplied by the residual value).
  
- `app.py`  
  A Streamlit-based user interface that allows users to either upload an input file (CSV/Excel) or enter item data manually. Users can set model parameters (baggage capacities, risk limit, penalty factor, mover's cost rate) via the sidebar and view assignment results.

## Input File Format

Your input file (CSV or Excel) should have the following columns:

- **Item**: The name of the item.
- **Monetary Value (INR)**: The original monetary value.
- **Weight (kg)**: The weight of the item.
- **Volume (liters)**: The volume of the item.
- **Age (years)**: The age of the item.
- **Depreciation per Year (%)**: The depreciation rate per year.
- **Airline Baggage Type**: Must be either "Hand Baggage" or "Check-in Baggage". This field determines which mode the item is allowed in.

## Default Parameters

The following defaults are used throughout the models and UI:

- **Cabin (Hand Baggage):**
  - Weight Capacity: **7.0 kg**
  - Volume Capacity: **34.0 liters**
- **Check-in Baggage:**
  - Weight Capacity: **23.0 kg**
  - Volume Capacity: **95.5 liters**
- **Risk Limit** (for movers): **50000.0** (total residual value)
- **Penalty Factor (alpha)**: **0.2**  
  (An extra cost of 20% of the item’s residual value is added when shipping via movers.)
- **Mover's Cost Rate**: **2.5 INR per liter**  
  (MoversCost is computed as: Volume (liters) × Mover's Cost Rate)

## Setup Instructions

1. **Create a Virtual Environment:**

    ```bash
    python -m venv venv
    ```

2. **Activate the Virtual Environment:**

   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

3. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```


## How to Run

### Running the Streamlit UI

Launch the UI with:

```bash
streamlit run app.py
