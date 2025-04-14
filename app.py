import streamlit as st
import pandas as pd
from dp_model import dp_solve
from ip_model import ip_solve
from csv_file_parser import parse_input_file

st.title("Multi-Bag Packing Optimization")

st.markdown("""
This application solves the multi-bag packing problem using either the Dynamic Programming (DP) or 
Integer Programming (IP) model.
  
**Input Data Requirements:**  
Your items should include the following information:  
- **Item** (name)  
- **Monetary Value (INR)**  
- **Weight (kg)**  
- **Volume (liters)**  
- **Age (years)**  
- **Depreciation per Year (%)**  
- **Airline Baggage Type** (e.g., "Hand Baggage" or "Check-in Baggage")
""")

# Sidebar for model parameters.
st.sidebar.header("Baggage & Model Parameters")
# Default capacity parameters (adjust as needed)
W_cabin    = st.sidebar.number_input("Cabin (Hand Baggage) Weight Capacity (kg)", value=7.0)
V_cabin    = st.sidebar.number_input("Cabin (Hand Baggage) Volume Capacity (liters)", value=34.0)
W_checkin  = st.sidebar.number_input("Check-in Weight Capacity (kg)", value=23.0)
V_checkin  = st.sidebar.number_input("Check-in Volume Capacity (liters)", value=95.5)
risk_limit = st.sidebar.number_input("Risk Limit (Total Residual Value)", value=50000.0)
alpha      = st.sidebar.number_input("Penalty Factor (alpha)", value=0.2)
movers_cost_rate = st.sidebar.number_input("Mover's Cost Rate (INR per liter)", value=2.5)
model_choice = st.sidebar.selectbox("Select Model", ("Dynamic Programming", "Integer Programming"))

# Sidebar: Choose input mode.
input_mode = st.sidebar.radio("Input Data Method", ("Upload CSV/Excel File", "Enter Data Manually"))

# Global variable (in session_state) to hold manual items
if "manual_items" not in st.session_state:
    st.session_state.manual_items = []

# Function to display the current table from manual inputs.
def display_manual_items():
    if st.session_state.manual_items:
        df_manual = pd.DataFrame(st.session_state.manual_items)
        st.subheader("Manual Items Data")
        st.dataframe(df_manual)
        return df_manual
    else:
        st.info("No manual items added yet.")
        return None

# ------------------------
# Input Mode: File Upload
# ------------------------
if input_mode == "Upload CSV/Excel File":
    st.header("Upload Items Data")
    uploaded_file = st.file_uploader("Upload Excel or CSV file", type=["xlsx", "csv"])
    if uploaded_file is not None:
        try:
            # Use file uploader data directly (BytesIO) with appropriate file type.
            if uploaded_file.name.endswith('.xlsx'):
                df_parsed = parse_input_file(uploaded_file, "excel", movers_cost_rate=movers_cost_rate,volume_checkin = V_checkin ,volume_cabin = V_cabin )
            else:
                df_parsed = parse_input_file(uploaded_file, "csv", movers_cost_rate=movers_cost_rate,volume_checkin = V_checkin ,volume_cabin = V_cabin )
            st.subheader("Parsed Items Data")
            st.dataframe(df_parsed)
        except Exception as e:
            st.error(f"Error parsing uploaded file: {e}")
    else:
        df_parsed = None

# ---------------------------
# Input Mode: Manual Entry
# ---------------------------
else:
    st.header("Enter Items Data Manually")
    with st.form("manual_input_form", clear_on_submit=True):
        item_name = st.text_input("Item Name")
        monetary_value = st.number_input("Monetary Value (INR)", min_value=0.0, step=100.0)
        weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1)
        volume = st.number_input("Volume (liters)", min_value=0.0, step=0.1)
        age = st.number_input("Age (years)", min_value=0, step=1)
        depreciation = st.number_input("Depreciation per Year (%)", min_value=0.0, step=0.1)
        baggage_type = st.selectbox("Airline Baggage Type", ("Hand Baggage", "Check-in Baggage"))
        submitted = st.form_submit_button("Add Item")
        if submitted and item_name:
            # Compute residual value.
            residual_value = monetary_value * (1 - (age * depreciation / 100.0))
            # Bundle data into a dictionary.
            manual_item = {
                "Item": item_name,
                "Monetary Value (INR)": monetary_value,
                "Weight (kg)": weight,
                "Volume (liters)": volume,
                "Age (years)": age,
                "Depreciation per Year (%)": depreciation,
                "Airline Baggage Type": baggage_type
            }
            st.session_state.manual_items.append(manual_item)
            st.success(f"Added item: {item_name}")
    df_manual = display_manual_items()
    # For consistency with the model, if manual input is used we convert items using our parser function.
    if df_manual is not None:
        # When using manual inputs, we already have most columns, but we can use our parser
        # to create the required columns (e.g., ResidualValue, MoversCost, SafeCabin, etc.)
        # For this purpose, we store the manual items temporarily in an excel-like buffer.
        # Alternatively, we could process df_manual inline.
        # Here, we simulate by writing and reading the DataFrame.
        df_manual["Monetary Value (INR)"] = df_manual["Monetary Value (INR)"].astype(float)
        # Use the manual DataFrame to compute required columns:
        # We simulate what parse_input_file does:
        df_manual["ResidualValue"] = df_manual.apply(
            lambda row: row["Monetary Value (INR)"] * (1 - (row["Age (years)"] * row["Depreciation per Year (%)"] / 100.0)),
            axis=1
        )
        df_manual["MoversCost"] = df_manual["Volume (liters)"] * movers_cost_rate
        df_manual["Weight"] = df_manual["Weight (kg)"]
        df_manual["Volume"] = df_manual["Volume (liters)"]
        def parse_baggage_type(bag_type):
            bag_type_lower = str(bag_type).strip().lower()
            if "hand" in bag_type_lower:
                return (1, 0)
            elif "check" in bag_type_lower:
                return (0, 1)
            return (0, 0)
        df_manual[['SafeCabin','SafeCheckin']] = df_manual.apply(
            lambda row: pd.Series(parse_baggage_type(row["Airline Baggage Type"])),
            axis=1
        )
        df_manual["SafeMovers"] = 1
        df_parsed = df_manual[['Weight','Volume','MoversCost','ResidualValue','SafeCabin','SafeCheckin','SafeMovers']]
        st.subheader("Processed Items Data")
        st.dataframe(df_parsed)

# ------------------------
# Solve Optimization
# ------------------------
if st.button("Solve Optimization"):
    if df_parsed is None:
        st.error("Please upload or enter the items data first.")
    else:
        if model_choice == "Dynamic Programming":
            st.write("Solving using the Dynamic Programming model...")
            total_cost, assignment = dp_solve(df_parsed, W_cabin, V_cabin, W_checkin, V_checkin, risk_limit, alpha)
            st.write("**Total Cost:**", total_cost)
            result_df = df_parsed.copy()
            # Append assignment results; manual mode does not include the original Item names so this is illustrative.
            result_df["Assignment"] = assignment
            st.subheader("Assignment Results")
            st.dataframe(result_df)
        else:
            st.write("Solving using the Integer Programming model...")
            status, total_cost, assignment = ip_solve(df_parsed, W_cabin, V_cabin, W_checkin, V_checkin, risk_limit, alpha)
            st.write("**Status:**", status)
            st.write("**Total Cost:**", total_cost)
            result_df = df_parsed.copy()
            result_df["Assignment"] = assignment
            st.subheader("Assignment Results")
            st.dataframe(result_df)
else:
    st.info("Provide input data using one of the two methods above, then click 'Solve Optimization'.")
