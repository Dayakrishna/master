import streamlit as st
import pandas as pd
from io import BytesIO
import os

st.set_page_config(page_title="Employees < 40 Hours (With Position)", layout="centered")

st.title("🔍 Employees with Less Than 40 Hours (Including 0 Hours)")

# Step 1: Check for cleaned file
if not os.path.exists("cleaned_data.xlsx"):
    st.error("❌ 'cleaned_data.xlsx' not found. Please run the data cleaning tool first.")
    st.markdown("⬅️ [Go to Upload Page](../Home)")
    st.stop()

# Step 2: Load cleaned Excel file
try:
    df = pd.read_excel("cleaned_data.xlsx")
except Exception as e:
    st.error(f"⚠️ Failed to read cleaned_data.xlsx: {e}")
    st.stop()

# Step 3: Validate required columns
required_cols = {"Employee Name", "Week Number", "Hours", "Position", "Team Name"}
if not required_cols.issubset(df.columns):
    st.warning(f"⚠️ Required columns missing. Found columns: {df.columns.tolist()}")
    st.stop()

# Step 4: Filter only employees with filled Position
df = df[df["Position"].notna() & (df["Position"].astype(str).str.strip() != "")]

# Step 5: Exclude "Before Week 1"
df = df[df["Week Number"] != "Before Week 1"]

# Step 6: Prepare full list of employee-week pairs
employees = df[["Employee Name", "Team Name", "Position"]].drop_duplicates()
weeks = df["Week Number"].drop_duplicates()
cross = employees.merge(weeks.to_frame(), how="cross")

# Step 7: Merge actual hours logged
actual_hours = df.groupby(["Employee Name", "Team Name", "Position", "Week Number"])["Hours"].sum().reset_index()
merged_df = pd.merge(cross, actual_hours, on=["Employee Name", "Team Name", "Position", "Week Number"], how="left")
merged_df["Hours"] = merged_df["Hours"].fillna(0)

# Step 8: Sort Week Number numerically
merged_df["Week_Num_Sort"] = merged_df["Week Number"].str.extract(r'Week (\d+)').astype(float)

# Step 9: Filter < 40 hours
below_40 = merged_df[merged_df["Hours"] < 40].sort_values(by=["Week_Num_Sort", "Employee Name"])

# Step 10: Display
if below_40.empty:
    st.success("✅ All employees with a valid Position logged ≥ 40 hours per week.")
else:
    st.markdown("### ⚠️ Employees with Less Than 40 Hours (Including 0)")
    st.dataframe(below_40.drop(columns=["Week_Num_Sort"]), use_container_width=True)

    # Step 11: Download option
    def convert_to_excel(dataframe):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            dataframe.to_excel(writer, index=False, sheet_name="Below 40 Hours")
        return output.getvalue()

    st.download_button(
        label="📥 Download < 40 Hours Report",
        data=convert_to_excel(below_40.drop(columns=["Week_Num_Sort"])),
        file_name="employees_below_40hrs_with_position.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
