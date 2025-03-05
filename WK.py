import streamlit as st
import pandas as pd
import datetime

# Streamlit App Title
st.title("Workload Distribution Dashboard")

# Upload First File (Workload Data)
st.subheader("Upload Workload Data")
workload_file = st.file_uploader("Upload the first Excel file (Workload Data)", type=["xlsx", "xls"])

# Upload Second File (Employee Details)
st.subheader("Upload Employee Details Data")
employee_file = st.file_uploader("Upload the second Excel file (Employee Details)", type=["xlsx", "xls"])

# Upload Third File (Additional Data if needed)
st.subheader("Upload Additional Data")
additional_file = st.file_uploader("Upload an additional Excel file", type=["xlsx", "xls"])

# Step 1: Load and Display Raw Additional Data
if additional_file:
    st.subheader("Step 1: Load and Display Raw Additional Data")

    # Read Additional Data
    df_additional = pd.read_excel(additional_file, dtype=str)

    # Display Raw Additional Data
    st.write("### Raw Additional Data (Before Cleaning)")
    st.dataframe(df_additional.head(10))  # Show first 10 rows

    # Step 2: Delete First Column (Column A) Before Cleaning
    st.subheader("Step 2: Delete First Column Before Cleaning")

    # Drop the first column (Column A)
    df_additional = df_additional.iloc[:, 1:]

    # Step 3: Remove First 3 Rows and Set Headers
    st.subheader("Step 3: Remove First 3 Rows and Set Headers")

    # Remove first 3 rows
    df_additional = df_additional.iloc[3:].reset_index(drop=True)

    # Set the 4th row (now index 0) as column headers
    df_additional.columns = df_additional.iloc[0]  # Use first row as headers
    df_additional = df_additional[1:].reset_index(drop=True)  # Remove the old header row

    # Drop duplicate column names (if any exist)
    df_additional = df_additional.loc[:, ~df_additional.columns.duplicated()]

    # Rename NaN columns to "Unnamed_X" to avoid errors
    df_additional.columns = [f"Unnamed_{i}" if pd.isna(col) else col for i, col in enumerate(df_additional.columns)]

    # Step 4: Remove Rows Where Column "Num" Has No Value
    st.subheader("Step 4: Remove Rows Where 'Num' is Empty")

    # Ensure "Num" column exists before filtering
    if "Num" in df_additional.columns:
        df_additional = df_additional[
            df_additional["Num"].notna() & (df_additional["Num"].astype(str).str.strip() != "")]
    else:
        st.warning("Column 'Num' not found in the dataset.")

    # Step 5: Keep Only Required Columns ("Num", "Amount", "Project Manager")
    st.subheader("Step 5: Keep Only 'Num', 'Amount', and 'Project Manager' Columns")

    # Ensure required columns exist before filtering
    required_columns = ["Num", "Amount", "Project Manager"]
    if all(col in df_additional.columns for col in required_columns):
        df_additional = df_additional[required_columns]
    else:
        missing_cols = [col for col in required_columns if col not in df_additional.columns]
        st.warning(f"Some required columns are missing: {missing_cols}. Keeping all columns.")

    # Step 6: Delete First Column Again **(Only if it is NOT 'Num')**
    st.subheader("Step 6: Delete First Column Again (If Not 'Num')")

    # Ensure we do not delete 'Num' by mistake
    if df_additional.columns[0] != "Num":
        df_additional = df_additional.iloc[:, 1:]
    else:
        st.info("Skipped deleting the first column because it's 'Num'.")

    # Step 7: Clean "Num" Column by Removing "1037-" Prefix
    st.subheader("Step 7: Remove '1037-' Prefix from 'Num' Column")

    # Ensure "Num" column exists before modifying
    if "Num" in df_additional.columns:
        df_additional["Num"] = df_additional["Num"].str.replace("^1037-", "",
                                                                regex=True)  # Removes "1037-" only if it appears at the start
    else:
        st.warning("Column 'Num' not found in the dataset.")
    if workload_file and employee_file:
        # Read Workload Data
        df_workload = pd.read_excel(workload_file, header=None, dtype=str)
        df_workload = df_workload.iloc[4:].reset_index(drop=True)  # Delete first 4 rows
        df_workload.iloc[:, 0] = df_workload.iloc[:, 0].fillna(method='ffill').str.replace("*", "",
                                                                                           regex=False).str.strip()

        # Set Headers for Workload Data
        workload_headers = ["Employee Name"] + df_workload.iloc[0, 1:].tolist()
        df_workload = df_workload[1:].reset_index(drop=True)
        df_workload.columns = [str(col).strip() for col in workload_headers]  # Trim column names

        # Read Employee Details Data
        df_employee = pd.read_excel(employee_file, dtype=str)
        df_employee.columns = [col.strip() for col in df_employee.columns]  # Trim column names

        # Debug: Print Column Names Before Merging
        st.write("🔍 Workload Data Columns:", df_workload.columns.tolist())
        st.write("🔍 Employee Data Columns:", df_employee.columns.tolist())

        # Ensure "Employee Name" exists before merging
        if "Employee Name" not in df_workload.columns:
            st.error("❌ 'Employee Name' missing in Workload Data!")
        if "Employee Name" not in df_employee.columns:
            st.error("❌ 'Employee Name' missing in Employee Data!")

        # ✅ Merge Workload & Employee Data (Already Fixed)
        if "Employee Name" in df_workload.columns and "Employee Name" in df_employee.columns:
            df_merged = df_workload.merge(df_employee, on="Employee Name", how="inner")
            st.success("✅ df_merged successfully created!")

            # ✅ Store df_merged in Session State for Analytics Page
            if "df_merged" not in st.session_state:
                st.session_state["df_merged"] = None  # Initialize if missing

            if df_merged is not None:
                st.session_state["df_merged"] = df_merged
                st.success("✅ df_merged stored successfully in session state!")
            else:
                st.warning("⚠️ df_merged could not be stored in session state. Check for issues in merging.")

            # ✅ Debugging: Show stored session data
            st.write("🔍 Debugging Session State:")
            st.write("df_additional stored:",
                     "✅ Available" if st.session_state.get('df_additional') is not None else "❌ Not Available")
            st.write("df_merged stored:",
                     "✅ Available" if st.session_state.get('df_merged') is not None else "❌ Not Available")
    # ✅ Step 1: Debugging `df_additional` Before Storing in Session State
    if additional_file:
        st.subheader("🔍 Step 1: Checking df_additional before storing...")

        if 'df_additional' in locals():
            st.write("✅ df_additional exists before session state storage!")
            st.write("🔍 df_additional Columns:", df_additional.columns.tolist())
            st.write("🔍 First 5 Rows:")
            st.dataframe(df_additional.head())  # Show first 5 rows to confirm data
        else:
            st.error("❌ df_additional is missing! Check data processing steps.")
    # ✅ Step 2: Store df_additional in Session State for Analytics Page
    if "df_additional" not in st.session_state:
        st.session_state["df_additional"] = None  # Initialize if missing

    if additional_file and "df_additional" in locals():
        st.session_state["df_additional"] = df_additional
        st.success("✅ df_additional stored successfully in session state!")
    else:
        st.warning(
            "⚠️ df_additional could not be stored in session state. Check for missing file or processing issues.")

    # ✅ Debugging: Show stored session data
    st.write("🔍 Debugging Session State:")
    st.write("df_additional stored:",
             "✅ Available" if st.session_state.get('df_additional') is not None else "❌ Not Available")
    st.write("df_merged stored:", "✅ Available" if st.session_state.get('df_merged') is not None else "❌ Not Available")

    # Display Final Cleaned Data
    st.write("### Final Cleaned Additional Data")
    st.dataframe(df_additional)  # Show full cleaned dataset

if workload_file and employee_file:
    # Read Workload Data
    df_workload = pd.read_excel(workload_file, header=None, dtype=str)
    df_workload = df_workload.iloc[4:].reset_index(drop=True)  # Delete first 4 rows
    df_workload.iloc[:, 0] = df_workload.iloc[:, 0].fillna(method='ffill').str.replace("*", "", regex=False).str.strip()

    # Set Headers for Workload Data
    workload_headers = ["Employee Name"] + df_workload.iloc[0, 1:].tolist()
    df_workload = df_workload[1:].reset_index(drop=True)
    df_workload.columns = [str(col).strip() for col in workload_headers]  # Trim column names

    # Remove Unwanted Columns
    columns_to_remove = ["Rates", "Billable", "Amount"]
    df_workload = df_workload.drop(columns=[col for col in columns_to_remove if col in df_workload.columns], errors="ignore")

    # Remove Rows Where "Product/Service" is Empty
    if "Product/Service" in df_workload.columns:
        df_workload = df_workload[df_workload["Product/Service"].notna() & (df_workload["Product/Service"].str.strip() != "")]

    # Convert "Activity Date" to Correct Format (DD-MM-YYYY)
    if "Activity Date" in df_workload.columns:
        def parse_date(date_str):
            try:
                if date_str.isnumeric() and len(date_str) > 10:
                    date_obj = pd.to_datetime(int(date_str), unit='ns')
                else:
                    date_obj = pd.to_datetime(date_str, errors='coerce', infer_datetime_format=True)
                return date_obj.strftime("%d-%m-%Y") if pd.notna(date_obj) else None
            except:
                return None

        df_workload["Activity Date"] = df_workload["Activity Date"].astype(str).apply(parse_date)

        # Add "Week Number" Column
        def calculate_week_number(date_str):
            try:
                if date_str:
                    date = datetime.datetime.strptime(date_str, "%d-%m-%Y")
                    week_1_start = datetime.datetime(2024, 12, 30)
                    return ((date - week_1_start).days // 7) + 1
            except:
                return None
            return None

        df_workload["Week Number"] = df_workload["Activity Date"].apply(calculate_week_number)

    # Normalize "Product/Service"
    if "Product/Service" in df_workload.columns:
        def normalize_product_service(value):
            if pd.isna(value):
                return value
            value = value.strip()

            if value.startswith("Internal:Self Development") or \
                    value.startswith("Internal:Internal Technical Project Discussion") or \
                    value.startswith("Internal:Admin - Meetings") or \
                    value.startswith("Internal:Administrative"):
                return "Administrative"
            elif value.startswith("Internal:Time off:"):
                return "Time off"
            elif value.startswith("Rates:") or "Senior Engineer" in value:
                return "Projects"
            return value

        df_workload["Product/Service"] = df_workload["Product/Service"].apply(normalize_product_service)
        # Modify Product/Service when Client starts with "Enerzinx LLC:"
        if "Client" in df_workload.columns and "Product/Service" in df_workload.columns:
            df_workload.loc[df_workload["Client"].str.startswith("Enerzinx LLC:",
                                                                 na=False), "Product/Service"] = "Internal Billable"

    # Read Employee Details Data
    df_employee = pd.read_excel(employee_file, dtype=str)
    df_employee.columns = [col.strip() for col in df_employee.columns]

    # Select Required Columns from Employee Data
    columns_to_merge = ["Employee Name", "Team Name", "Position", "USD per Hour", "Work_Week_Percentage", "USD Calculation"]
    df_employee = df_employee[columns_to_merge]

    # Merge Workload Data with Employee Data
    df_merged = df_workload.merge(df_employee, on="Employee Name", how="inner")

    # Convert Numeric Columns
    for col in df_merged.columns:
        try:
            df_merged[col] = pd.to_numeric(df_merged[col], errors='ignore')
        except:
            pass

    # **Create Weekly Summary**
    df_summary = df_employee.copy()
    max_week = df_merged["Week Number"].max()

    # Group by Employee Name and Summarize Duration for Projects
    df_projects = df_merged[df_merged["Product/Service"] == "Projects"]
    df_projects_summary = df_projects.groupby(["Employee Name", "Week Number"])["Duration"].sum().unstack(fill_value=0)
    df_projects_summary.columns = [f"Week {col}" for col in df_projects_summary.columns]

    # Group by Employee Name and Summarize Time Off Duration
    df_time_off = df_merged[df_merged["Product/Service"] == "Time off"]
    df_time_off_summary = df_time_off.groupby(["Employee Name", "Week Number"])["Duration"].sum().unstack(fill_value=0)
    df_time_off_summary.columns = [f"Av Week {col}" for col in df_time_off_summary.columns]

    # Merge with Employee Data
    df_summary = df_summary.merge(df_projects_summary, on="Employee Name", how="left").fillna(0)
    df_summary = df_summary.merge(df_time_off_summary, on="Employee Name", how="left").fillna(0)

    # Calculate "Av Week X" as 40 - (Time Off Hours)
    for week in range(1, max_week + 1):
        df_summary[f"Av Week {week}"] = 40 - df_summary.get(f"Av Week {week}", 0)

    # Ensure "USD per Hour" is Numeric
    df_summary["USD per Hour"] = pd.to_numeric(df_summary["USD per Hour"], errors="coerce").fillna(0)

    # Calculate Target Achieved as sum of (Week X * USD per Hour)
    df_summary["Target Achieved"] = sum(
        df_summary.get(f"Week {week}", 0) * df_summary["USD per Hour"] for week in range(1, max_week + 1)
    )

    # **Create Team Summary**
    df_team_summary = df_summary.groupby("Team Name").agg({"Target Achieved": "sum"}).reset_index()
    team_target_values = {
        "Sagar & Team": 2020408.16,
        "Vinoth & Team": 1653061.22,
        "Dr. Suresh & Team": 1959183.67,
        "Praveen & Team": 2693877.55,
        "Jigar & Team": 673469.39
    }
    df_team_summary["Team Target"] = df_team_summary["Team Name"].map(team_target_values)
    df_team_summary["Remaining Target"] = df_team_summary["Team Target"] - df_team_summary["Target Achieved"]

    # Add Total Row (EZX Team)
    total_row = pd.DataFrame({
        "Team Name": ["EZX Team"],
        "Target Achieved": [df_team_summary["Target Achieved"].sum()],
        "Team Target": [df_team_summary["Team Target"].sum()],
        "Remaining Target": [df_team_summary["Remaining Target"].sum()]
    })
    df_team_summary = pd.concat([df_team_summary, total_row], ignore_index=True)

    # Save & Download Button
    output_file = "Workload_Summary.xlsx"
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        df_merged.to_excel(writer, sheet_name="Master Data", index=False)
        df_summary.to_excel(writer, sheet_name="Weekly Summary", index=False)
        df_team_summary.to_excel(writer, sheet_name="Team Summary", index=False)

    with open(output_file, "rb") as f:
        st.download_button("Download Processed Excel File", f, "Workload_Summary.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # Display Data
    st.subheader("Weekly Summary")
    st.dataframe(df_summary)
    st.subheader("Team Summary")
    st.dataframe(df_team_summary)

    # **Extra Download Button at Bottom**
    with open(output_file, "rb") as f:
        st.download_button("⬇️ Download Again", f, "Workload_Summary.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
# Dashboard Navigation Button
st.page_link("pages/dashboard.py", label="📊 Go to Dashboard", icon="📊")

st.markdown("[📊 Go to Dashboard](http://localhost:8501/dashboard)", unsafe_allow_html=True)
# Navigation Button to Analytics Page
st.page_link("pages/analytics.py", label="📊 Go to Analytics", icon="📊")

st.markdown("[📊 Go to Analytics](http://localhost:8501/analytics)", unsafe_allow_html=True)
