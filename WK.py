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
