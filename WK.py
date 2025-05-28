import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import re

# --- CONFIG ---
st.set_page_config(page_title="QuickBooks Timesheet Cleaner", layout="centered")

from PIL import Image

logo_image = Image.open("logo.png")
st.sidebar.image(logo_image, width=180)

# --- HEADER ---
logo_url = Image.open("logo.png")
st.markdown(
    f"""
    <div style='display: flex; align-items: center; justify-content: space-between;'>
        <img src="{logo_url}" width="180">
        <h2 style='color: #2c3e50;'>QuickBooks Timesheet Data Cleaning</h2>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")

# --- FILE UPLOADS ---
st.subheader("📤 Upload Your QuickBooks Timesheet File")
uploaded_file = st.file_uploader("Choose Excel or CSV file", type=["xlsx", "xls", "csv"], key="timesheet")

st.subheader("📤 Upload Designation Mapping File")
designation_file = st.file_uploader("Upload Designation Excel (Employee Name, Team Name, Position, USD/Hr)", type=["xlsx", "xls"], key="designation")

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file, skiprows=4)
    else:
        df = pd.read_excel(uploaded_file, skiprows=4)

    original_columns = df.columns.tolist()
    if original_columns:
        df.rename(columns={original_columns[0]: "Employee Name"}, inplace=True)

    if "Employee Name" in df.columns:
        df["Employee Name"] = df["Employee Name"].fillna(method="ffill")
        df["Employee Name"] = df["Employee Name"].str.replace(r"^\*", "", regex=True).str.strip()

    if "Product/Service full name" in df.columns:
        df["Product/Service full name"] = df["Product/Service full name"].str.replace(r"^Internal:", "", regex=True).str.strip()
        df["Product/Service full name"] = df["Product/Service full name"].apply(
            lambda x: "Time off" if str(x).strip().startswith("Time off:") else x
        )
        roles_to_convert = [
            "Rates:Application Engineer I", "Rates:Senior Engineer I", "Rates:Application Engineer II",
            "Rates:Principal Engineer I", "Rates:Senior Director", "Rates:Intern",
            "Rates:Director/Principal Engineer- II", "Rates:Admin Assistant", "Rates:Senior Engineer II",
            "Rates:Assistant Application Engineer", "Rates:CAD Designer"
        ]
        df["Product/Service full name"] = df["Product/Service full name"].apply(
            lambda x: "Projects" if str(x).strip() in roles_to_convert else x
        )

    if "Client full name" in df.columns and "Product/Service full name" in df.columns:
        df["Product/Service full name"] = df.apply(
            lambda row: "Internal Billable"
            if str(row["Client full name"]).startswith("Enerzinx LLC:") else row["Product/Service full name"],
            axis=1
        )

    if "Activity date" in df.columns:
        df["Activity date"] = pd.to_datetime(df["Activity date"], format="%m/%d/%Y", errors="coerce")
        df["Activity date"] = df["Activity date"].dt.strftime("%d/%m/%Y")
        base_date = datetime.strptime("30/12/2024", "%d/%m/%Y")
        activity_dates = pd.to_datetime(df["Activity date"], format="%d/%m/%Y", errors="coerce")
        df["Week Number"] = activity_dates.apply(lambda d: f"Week {(d - base_date).days // 7 + 1}" if pd.notnull(d) and (d - base_date).days >= 0 else "Before Week 1")

    # --- Merge Designation File ---
    if designation_file:
        try:
            designation_df = pd.read_excel(designation_file)
            if "Employee Name" in designation_df.columns:
                designation_df["Employee Name"] = designation_df["Employee Name"].str.strip()
                designation_df = designation_df[["Employee Name", "Team Name", "Position", "USD/Hr"]]
                df = pd.merge(df, designation_df, how="left", on="Employee Name")
                st.success("✅ Designation data merged successfully.")
            else:
                st.error("❌ 'Employee Name' not found in designation file.")
        except Exception as e:
            st.error(f"❌ Error reading designation file: {e}")

    def parse_duration_to_hours(duration_str):
        try:
            if pd.isnull(duration_str):
                return 0
            if isinstance(duration_str, (float, int)):
                return float(duration_str)
            match = re.match(r'^\s*(\d{1,2}):(\d{2})\s*$', str(duration_str).strip())
            if match:
                return int(match.group(1)) + int(match.group(2)) / 60
            return 0
        except:
            return 0

    if "Duration" in df.columns:
        df["Hours"] = df["Duration"].apply(parse_duration_to_hours)
        if "USD/Hr" in df.columns and "Product/Service full name" in df.columns:
            df["Projects USD"] = df.apply(
                lambda row: row["USD/Hr"] * row["Hours"] if row["Product/Service full name"] == "Projects" else 0,
                axis=1
            )
            df["Projects USD"] = df["Projects USD"].round(2)

    st.success("✅ Data cleaned successfully.")
    st.write("### 🔍 Preview of Cleaned Data", df.head())

    # Optional tools
    st.markdown("### ✨ Optional Cleaning Tools")
    if st.checkbox("Trim Whitespace from All Text Columns"):
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        st.success("Whitespace trimmed.")

    missing_action = st.selectbox("Handle Missing Values", ["Do Nothing", "Fill with 'Unknown'", "Fill with 0", "Drop Rows"])
    if missing_action == "Fill with 'Unknown'":
        df = df.fillna("Unknown")
    elif missing_action == "Fill with 0":
        df = df.fillna(0)
    elif missing_action == "Drop Rows":
        df = df.dropna()

    if st.checkbox("Remove Duplicate Rows"):
        df = df.drop_duplicates()
        st.success("Duplicates removed.")

    st.write("### 🧾 Final Cleaned Data Preview", df.head())

    # Download Cleaned File
    def convert_df_to_excel(dataframe):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            dataframe.to_excel(writer, index=False)
        return output.getvalue()

    st.download_button(
        label="📥 Download Cleaned File",
        data=convert_df_to_excel(df),
        file_name="cleaned_timesheet.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Save to session state and file
    try:
        if (
            "Projects USD" in df.columns and
            designation_file is not None and
            'designation_df' in locals() and
            "Employee Name" in designation_df.columns
        ):
            st.session_state["cleaned_df"] = df.copy()
            st.session_state["designation_df"] = designation_df.copy()

            # ✅ Save cleaned file to disk for dashboard fallback
            df.to_excel("cleaned_data.xlsx", index=False)

            st.markdown("---")
            st.success("✅ Data prepared and stored for dashboard access.")
            st.page_link("1_Dashboard", label="📊 Go to Team Dashboard", icon="📈")
    except Exception as e:
        st.warning(f"⚠️ Could not prepare dashboard view: {e}")
else:
    st.info("Please upload a QuickBooks timesheet to begin.")
