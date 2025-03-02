import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Load Processed Excel File
file_path = "Workload_Summary.xlsx"


@st.cache_data
def load_data():
    return pd.read_excel(file_path, sheet_name=None)


# Load Data
data = load_data()
df_master = data["Master Data"]

# Ensure "Activity Date" is converted to datetime format
df_master["Activity Date"] = pd.to_datetime(df_master["Activity Date"], format="%d-%m-%Y", errors='coerce')

# Calculate "Week Number"
df_master["Week Number"] = df_master["Activity Date"].dt.isocalendar().week

# Filter Relevant Columns
df_master = df_master[["Employee Name", "Team Name", "Position", "Week Number", "Product/Service", "Duration"]]

# Get the latest available week
latest_week = df_master["Week Number"].max()
df_latest_week = df_master[df_master["Week Number"] == latest_week]

# Define color mapping for Positions (Consistent Across All Graphs)
position_colors = {
    "INTERN": "#0033CC",  # Blue
    "TL": "#FF9900",  # Orange
    "ATL": "#666666",  # Gray
    "TM": "#FFD700"  # Gold/Yellow
}

### **1️⃣ Work Distribution by Position (Corrected Calculation)**
# **Get Employee Count Per Position**
df_employee_count = df_latest_week.groupby("Position")["Employee Name"].nunique().reset_index()
df_employee_count["Available Hours"] = df_employee_count["Employee Name"] * 40  # Employees × 40 hours

# **Summarize Duration by Position & Product/Service**
df_summary_pos = df_latest_week.groupby(["Position", "Product/Service"])["Duration"].sum().reset_index()

# **Merge with Available Hours for Normalization**
df_summary_pos = df_summary_pos.merge(df_employee_count, on="Position", how="left")

# **Calculate Corrected Percentage**
df_summary_pos["Percentage"] = (df_summary_pos["Duration"] / df_summary_pos["Available Hours"]) * 100

# **Create Pivot Table**
df_pivot_pos = df_summary_pos.pivot(index="Product/Service", columns="Position", values="Percentage").fillna(0)

# **Sort by Highest Contribution**
df_pivot_pos["Max Value"] = df_pivot_pos.max(axis=1)
df_pivot_pos = df_pivot_pos.sort_values(by="Max Value", ascending=False).drop(columns=["Max Value"])

# **Plot the Work Distribution by Position**
fig_pos = go.Figure()
for position in df_pivot_pos.columns:
    fig_pos.add_trace(go.Bar(
        x=df_pivot_pos.index,
        y=df_pivot_pos[position],
        name=position,
        marker_color=position_colors.get(position, "lightgray"),
        text=df_pivot_pos[position].apply(lambda x: f"{x:.1f}%" if x > 0 else ""),
        textposition="outside",
    ))

fig_pos.update_layout(
    title=f"Work Distribution by Position - Week {latest_week}",
    xaxis_title="Product/Service",
    yaxis_title="Percentage",
    barmode="group",
    template="plotly_white",
    xaxis=dict(tickangle=-30, tickfont=dict(size=12)),
    yaxis=dict(range=[0, 100], showgrid=True, gridcolor="lightgray"),
    legend_title="Position",
    margin=dict(l=40, r=40, t=40, b=120),
    bargap=0.3,
)

st.plotly_chart(fig_pos, use_container_width=True)
st.subheader(f"Work Distribution Data by Position for Week {latest_week}")
st.dataframe(df_pivot_pos.T.reset_index())

### **2️⃣ Work Distribution by Team (Normalized Calculation)**
# **Get Employee Count Per Team**
df_employee_count_team = df_latest_week.groupby("Team Name")["Employee Name"].nunique().reset_index()
df_employee_count_team["Available Hours"] = df_employee_count_team["Employee Name"] * 40  # Employees × 40 hours

# **Summarize Duration by Team & Product/Service**
df_summary_team = df_latest_week.groupby(["Team Name", "Product/Service"])["Duration"].sum().reset_index()

# **Merge with Available Hours for Normalization**
df_summary_team = df_summary_team.merge(df_employee_count_team, on="Team Name", how="left")

# **Calculate Corrected Percentage**
df_summary_team["Percentage"] = (df_summary_team["Duration"] / df_summary_team["Available Hours"]) * 100

# **Create Pivot Table**
df_pivot_team = df_summary_team.pivot(index="Product/Service", columns="Team Name", values="Percentage").fillna(0)

# **Sort by Highest Contribution**
df_pivot_team["Max Value"] = df_pivot_team.max(axis=1)
df_pivot_team = df_pivot_team.sort_values(by="Max Value", ascending=False).drop(columns=["Max Value"])

# **Plot the Work Distribution by Team**
fig_team = go.Figure()
for team in df_pivot_team.columns:
    fig_team.add_trace(go.Bar(
        x=df_pivot_team.index,
        y=df_pivot_team[team],
        name=team,
        text=df_pivot_team[team].apply(lambda x: f"{x:.1f}%" if x > 0 else ""),
        textposition="outside",
    ))

fig_team.update_layout(
    title=f"Work Distribution by Team - Week {latest_week}",
    xaxis_title="Product/Service",
    yaxis_title="Percentage",
    barmode="group",
    template="plotly_white",
    xaxis=dict(tickangle=-30, tickfont=dict(size=12)),
    yaxis=dict(range=[0, 100], showgrid=True, gridcolor="lightgray"),
    legend_title="Team",
    margin=dict(l=40, r=40, t=40, b=120),
    bargap=0.3,
)

st.plotly_chart(fig_team, use_container_width=True)
st.subheader(f"Work Distribution Data by Team for Week {latest_week}")
st.dataframe(df_pivot_team.T.reset_index())

### **3️⃣ Work Distribution by Position Within Each Team**
st.subheader(f"📊 Work Distribution by Position Within Each Team - Week {latest_week}")

for team in df_master["Team Name"].unique():
    df_team_pos = df_latest_week[df_latest_week["Team Name"] == team]
    df_summary_team_pos = df_team_pos.groupby(["Position", "Product/Service"])["Duration"].sum().reset_index()

    # **Get Employee Count Per Position Within Team**
    df_employee_count_team_pos = df_team_pos.groupby("Position")["Employee Name"].nunique().reset_index()
    df_employee_count_team_pos["Available Hours"] = df_employee_count_team_pos[
                                                        "Employee Name"] * 40  # Employees × 40 hours

    # **Merge with Available Hours for Normalization**
    df_summary_team_pos = df_summary_team_pos.merge(df_employee_count_team_pos, on="Position", how="left")

    # **Calculate Corrected Percentage**
    df_summary_team_pos["Percentage"] = (df_summary_team_pos["Duration"] / df_summary_team_pos["Available Hours"]) * 100

    # **Create Pivot Table**
    df_pivot_team_pos = df_summary_team_pos.pivot(index="Product/Service", columns="Position",
                                                  values="Percentage").fillna(0)

    # **Plot Work Distribution by Position for Each Team**
    fig_team_pos = go.Figure()
    for position in df_pivot_team_pos.columns:
        fig_team_pos.add_trace(go.Bar(
            x=df_pivot_team_pos.index,
            y=df_pivot_team_pos[position],
            name=position,
            marker_color=position_colors.get(position, "lightgray"),
            text=df_pivot_team_pos[position].apply(lambda x: f"{x:.1f}%" if x > 0 else ""),
            textposition="outside",
        ))

    fig_team_pos.update_layout(
        title=f"Work Distribution by Position - {team} - Week {latest_week}",
        xaxis_title="Product/Service",
        yaxis_title="Percentage",
        barmode="group",
        template="plotly_white",
        xaxis=dict(tickangle=-30, tickfont=dict(size=12)),
        yaxis=dict(range=[0, 100], showgrid=True, gridcolor="lightgray"),
        legend_title="Position",
        margin=dict(l=40, r=40, t=40, b=120),
        bargap=0.3,
    )

    st.plotly_chart(fig_team_pos, use_container_width=True)
