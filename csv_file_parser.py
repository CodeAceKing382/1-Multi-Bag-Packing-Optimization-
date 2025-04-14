# csv_file_parser.py

import pandas as pd

def parse_input_file(file_path, file_type="csv", movers_cost_rate=10,volume_checkin = 95.5 ,volume_cabin = 34 ):
    """
    Reads the input CSV/Excel file and generates a Pandas DataFrame
    that includes the columns required by the DP/IP solvers:
      Weight, Volume, MoversCost, ResidualValue, SafeCabin, SafeCheckin, SafeMovers.
    
    MoversCost is computed based on item volume:
    
        MoversCost = Volume (liters) * movers_cost_rate

    :param file_path: Path to the input file.
    :param file_type: "csv" or "excel" (defaults to "csv").
    :param movers_cost_rate: The cost per unit volume for movers (e.g., INR per liter).
    :return: DataFrame with the needed columns.
    """
    if file_type.lower() == "excel" or file_path.lower().endswith(".xlsx"):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path)

    # Expected input columns:
    # "Item", "Monetary Value (INR)", "Weight (kg)", "Volume (liters)",
    # "Age (years)", "Depreciation per Year (%)", "Airline Baggage Type"

    # 1) Compute ResidualValue:
    df['ResidualValue'] = df.apply(
        lambda row: row['Monetary Value (INR)'] * (1 - (row['Age (years)'] * row['Depreciation per Year (%)'] / 100.0)),
        axis=1
    )

    # 2) Compute MoversCost using volume-based pricing.
    df['MoversCost'] = df['Volume (liters)'] * movers_cost_rate

    # 3) Copy Weight and Volume.
    df['Weight'] = df['Weight (kg)']
    df['Volume'] = df['Volume (liters)']

    # 4) Define SafeCabin and SafeCheckin based on "Airline Baggage Type".
    def parse_baggage_type(bag_type):
        bag_type_lower = str(bag_type).strip().lower()
        if "hand" in bag_type_lower:
            return (1, 0)
        elif "check" in bag_type_lower:
            return (0, 1)
        return (0, 0)

    df[['SafeCabin', 'SafeCheckin']] = df.apply(
        lambda row: pd.Series(parse_baggage_type(row['Airline Baggage Type'])),
        axis=1
    )

    df.loc[(df['SafeCheckin'] == 1) & (df['Volume'] > volume_checkin), 'SafeCheckin'] = 0

    df.loc[(df['SafeCabin'] == 1) & (df['Volume'] > volume_cabin), 'SafeCabin'] = 0

    # 5) All items can be sent via movers.
    df['SafeMovers'] = 1

    # 6) Return only the required columns.
    final_df = df[['Item','Weight', 'Volume', 'MoversCost', 'ResidualValue',
                   'SafeCabin', 'SafeCheckin', 'SafeMovers']].copy()
    return final_df

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Parse CSV/Excel file for Multi-Bag Packing inputs.")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV or Excel file")
    parser.add_argument("--file_type", type=str, default="csv", help="File type: 'csv' or 'excel'")
    parser.add_argument("--rate", type=float, default=10.0, help="Mover's cost per liter (default 10 INR/liter)")
    args = parser.parse_args()

    try:
        final_df = parse_input_file(args.input, args.file_type, movers_cost_rate=args.rate)
        print("Parsed DataFrame:")
        print(final_df.head())
    except Exception as e:
        print("Error parsing file:", e)
