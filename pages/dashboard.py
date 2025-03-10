import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


# Set Page Configurations
st.set_page_config(page_title="Workload Dashboard", layout="wide")

with st.sidebar:
    st.image("logo.png", width=150)  # Sidebar logo
    st.markdown("## Navigation")
# Load Processed Excel File
file_path = "Workload_Summary.xlsx"

@st.cache_data
def load_data():
    return pd.read_excel(file_path, sheet_name=None)

data = load_data()
df_team = data["Team Summary"]  # Load Team Summary Sheet

# Sidebar Navigation (Collapsed by Default)
# Sidebar Navigation (Collapsed by Default)
with st.sidebar.expander("📊 Navigation", expanded=False):
    team_names = ["EZX Team Summary", "Sagar", "Vinoth", "Dr. Suresh", "Praveen", "Jigar", "📊 Data Check"]
    selected_team = st.radio("Select a Section:", team_names, index=0)


# Function to Get Team Data
def get_team_data(team_name):
    return df_team[df_team["Team Name"].str.contains(team_name, case=False)].iloc[0]  # Fetch first row

# **EZX Team Summary**
if selected_team == "EZX Team Summary":
    # Fetch EZX Team Data
    ezx_data = get_team_data("EZX Team")
    total_achieved = ezx_data["Target Achieved"]
    total_target = ezx_data["Team Target"]
    percentage = (total_achieved / total_target) * 100 if total_target else 0

    # **Aligned Header Layout**
    col1, col2, col3, col4, col5, col6 = st.columns([1.8, 1, 1, 1, 1, 1])

    with col1:
        st.markdown(f"""
            <style>
            .flip-box {{
                font-size: 120px;  /* Very Large Flip Counter */
                font-weight: bold;
                text-align: left;
                color: black;
                line-height: 1;
            }}
            .title-text {{
                font-size: 24px;
                font-weight: bold;
            }}
            </style>
            <div class="title-text">EZX Team</div>
            <div class="flip-box">{percentage:.1f}%</div>
        """, unsafe_allow_html=True)

    # **Pie Charts for Each Team with Custom Colors & Inside Vertical Legends**
    team_list = ["Dr. Suresh", "Sagar", "Vinoth", "Praveen", "Jigar"]
    team_colors = ["#00A6A6", "#F76C6C", "#FFB400", "#6B4226", "#636EFA"]  # Custom Colors
    cols = [col2, col3, col4, col5, col6]

    for i, team in enumerate(team_list):
        with cols[i]:
            team_data = get_team_data(team)
            achieved = team_data["Target Achieved"]
            remaining = team_data["Remaining Target"]

            # Pie Chart with Achieved % in the Colored Part & Remaining % in Gray
            fig = go.Figure(data=[
                go.Pie(
                    labels=["Achieved", "Remaining"],
                    values=[achieved, remaining],
                    hole=0.4,
                    textinfo="none",  # ✅ Hide all values & percentages
                    hoverinfo="none",  # ✅ Disable hover values
                    marker=dict(colors=[team_colors[i], "#D3D3D3"]),  # Custom Colors
                )
            ])

            # Set Layout for Compact Display & Percentage Inside Correct Sections
            fig.update_layout(
                annotations=[
                    dict(
                        text=f"<b>{team}</b>",  # Team Name Inside Pie Chart
                        x=0.5, y=0.5,
                        font=dict(size=18, color="black"),
                        showarrow=False
                    ),
                    dict(
                        text=f"Remaining {remaining / (achieved + remaining) * 100:.1f}%",  # Achieved % inside colored part
                        x=0.30, y=0.30,
                        font=dict(size=10, color="black", family="Arial Black"),  # Bold White for visibility
                        showarrow=False
                    ),
                    dict(
                        text=f"{achieved / (achieved + remaining) * 100:.1f}%",  # Remaining % inside gray part
                        x=0.31, y=0.65,
                        font=dict(size=12, color="white", family="Arial Black"),  # Bold Black for contrast
                        showarrow=False
                    )
                ],
                margin=dict(l=0, r=0, t=0, b=0),  # Remove Extra Spacing
                showlegend=False  # Remove Legends Outside
            )

            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})  # No Download Button

else:
    # Show Selected Team Data
    pass

# Back to Upload Page
st.sidebar.markdown("[⬅ Back to Upload Page](http://localhost:8501/)", unsafe_allow_html=True)



# Load Weekly Summary Data
df_weekly = data["Weekly Summary"]

# **Function to Get Weekly Data for the Selected Team**
def get_weekly_team_data(team_name):
    # Filter data for the selected team
    team_data = df_weekly[df_weekly["Team Name"].str.contains(team_name, case=False, na=False)]

    if team_data.empty:
        return None  # Return None if no data found

    # Extract Available Hours & Actual Work Done (Week Columns)
    week_columns = [col for col in team_data.columns if col.startswith("Week ") and not col.endswith("Project %")]
    av_week_columns = [col.replace("Week ", "Av Week ") for col in week_columns]

    # Aggregate Data for the Selected Team
    weekly_summary = team_data[week_columns].sum()
    available_summary = team_data[av_week_columns].sum()

    # Create DataFrame for Chart
    df_chart = pd.DataFrame({
        "Week Number": [f"Week {i+1}" for i in range(len(week_columns))],  # X-axis Labels
        "Available Hours": available_summary.values,
        "Actual Work Done": weekly_summary.values
    })
    return df_chart

# **Include Insight Chart for Selected Team**
if selected_team in team_names and selected_team != "EZX Team Summary":
    st.markdown(f"### 📊 {selected_team} - Weekly Performance Insights")

    # Get Weekly Data for Selected Team
    df_insights = get_weekly_team_data(selected_team)

    if df_insights is not None:
        # Create a Stacked Bar Chart
        fig = px.bar(
            df_insights,
            x="Week Number",
            y=["Available Hours", "Actual Work Done"],
            labels={"value": "Hours", "Week Number": "Week"},
            title=f"{selected_team} Weekly Performance",
            barmode="group",
            text_auto=True
        )

        # Add a Trend Line for Actual Work Done
        fig.add_scatter(x=df_insights["Week Number"], y=df_insights["Actual Work Done"],
                        mode="lines+markers", name="Trend Line",
                        line=dict(color="red", width=3))

        # Display the Chart
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.warning(f"No weekly data found for {selected_team}.")

# **Function to Get Work Distribution for a Selected Team in Percentage**
def get_team_work_distribution_percentage(team_name):
    # Load Master Data
    df_master = data["Master Data"]

    # Filter for the Selected Team
    df_filtered = df_master[df_master["Team Name"].str.contains(team_name, case=False, na=False)]

    if df_filtered.empty:
        return None  # Return None if no data found

    # Summing Up the Duration for Each Product/Service
    df_distribution = df_filtered.groupby("Product/Service")["Duration"].sum().reset_index()

    # **Calculate Total Hours Worked**
    total_hours = df_distribution["Duration"].sum()

    # **Convert Duration to Percentage**
    df_distribution["Percentage"] = (df_distribution["Duration"] / total_hours) * 100

    # Sort Data in Descending Order
    df_distribution = df_distribution.sort_values(by="Percentage", ascending=False)

    return df_distribution

# **Generate Work Distribution Chart for Individual Teams**
if selected_team in team_names and selected_team != "EZX Team Summary":
    st.subheader(f"📊 Work Distribution Across Product/Services - {selected_team} (in %)")


    # Fetch Work Distribution Data
    df_team_distribution = get_team_work_distribution_percentage(selected_team)

    if df_team_distribution is not None and not df_team_distribution.empty:
        # **Create a Horizontal Bar Chart**
        fig_distribution = go.Figure()

        fig_distribution.add_trace(go.Bar(
            y=df_team_distribution["Product/Service"],
            x=df_team_distribution["Percentage"],
            text=df_team_distribution["Percentage"].apply(lambda x: f"{x:.1f}%"),  # Show Percentage
            textposition='auto',
            orientation='h',  # Horizontal Bar Chart
            marker=dict(color="royalblue")  # Custom Color
        ))

        # **Customize Layout**
        fig_distribution.update_layout(
            xaxis_title="Work Distribution (%)",
            yaxis_title="Product/Service",
            title=f"Work Distribution Across Product/Services for {selected_team} (in %)",
            template="plotly_white"
        )

        # **Show Chart in Streamlit**
        st.plotly_chart(fig_distribution, use_container_width=True)

    else:
        st.warning(f"No work distribution data found for {selected_team}.")

#starts



# Load Processed Excel File
file_path = "Workload_Summary.xlsx"

@st.cache_data
def load_data():
    return pd.read_excel(file_path, sheet_name=None)

data = load_data()
df_weekly = data["Weekly Summary"]  # Weekly Summary Sheet

# Identify week columns dynamically
week_columns = [col for col in df_weekly.columns if col.startswith("Week ")]
av_week_columns = [col for col in df_weekly.columns if col.startswith("Av Week ")]

# Extract relevant columns
df_weekly_summary = df_weekly[["Team Name"] + week_columns + av_week_columns]

# Group by team name and sum the weekly data
df_team_weekly = df_weekly_summary.groupby("Team Name").sum()

# Calculate productivity percentage (Actual Work Done / Available Hours) * 100
df_productivity = pd.DataFrame()

for team in df_team_weekly.index:
    actual_work = df_team_weekly.loc[team, week_columns]
    available_hours = df_team_weekly.loc[team, av_week_columns]

    # Ensure matching week numbers for available hours
    available_hours.index = week_columns  # Rename to match
    productivity = (actual_work / available_hours) * 100
    df_productivity[team] = productivity

# Reset index for plotting
df_productivity = df_productivity.T

# Create an interactive figure
# 📊 Weekly Productivity Insights
if selected_team in team_names:
    st.subheader(f"📊 Weekly Productivity for {selected_team}")

    # Ensure Data Exists
    if df_productivity.empty:
        st.warning("No productivity data available.")
    else:
        # Ensure team names are properly matched
        matching_teams = [team for team in df_productivity.index if selected_team.lower().strip() in team.lower().strip()]

        if selected_team == "EZX Team Summary":
            df_productivity_chart = df_productivity.copy()  # Show all teams in EZX summary
        elif matching_teams:
            df_productivity_chart = df_productivity.loc[matching_teams]  # Show only matching team
        else:
            df_productivity_chart = pd.DataFrame()  # Empty if no match

        # Check if filtered DataFrame is empty
        if df_productivity_chart.empty:
            st.warning(f"⚠ No weekly data available for {selected_team}. Check if the team name matches exactly in the dataset.")
        else:
            # Create an Interactive Figure
            fig = go.Figure()

            # Add Line for Each Team (All teams in "EZX Team Summary" OR Single team in individual pages)
            for team in df_productivity_chart.index:
                fig.add_trace(go.Scatter(
                    x=df_productivity_chart.columns,  # Week numbers as x-axis
                    y=df_productivity_chart.loc[team],  # Productivity % as y-axis
                    mode="lines+markers",
                    name=team,
                    line=dict(width=3 if team == selected_team else 1.5, dash="solid"),  # Thicker line for selected team
                    marker=dict(size=8 if team == selected_team else 6),
                ))

            # **Add a Dotted Reference Line at 75%**
            fig.add_shape(
                type="line",
                x0=df_productivity_chart.columns[0],  # Start from first week
                x1=df_productivity_chart.columns[-1],  # End at last week
                y0=75,
                y1=75,
                line=dict(color="red", width=2, dash="dot"),  # Red dotted line for threshold
            )

            # Customize Layout
            fig.update_layout(
                title=f"Weekly Productivity Across Teams" if selected_team == "EZX Team Summary" else f"Weekly Productivity - {selected_team}",
                xaxis_title="Week",
                yaxis_title="Productivity (%)",
                legend_title="Team" if selected_team == "EZX Team Summary" else None,
                template="plotly_white",
                xaxis=dict(tickangle=-45, tickfont=dict(size=12)),
                yaxis=dict(showgrid=True, gridcolor="lightgray", range=[0, 100]),  # Ensure y-axis goes up to 100%
            )

            # Show Interactive Chart in Streamlit
            st.plotly_chart(fig, use_container_width=True)



# **Overall Productivity Chart (Only in "EZX Team Summary" Page)**
if selected_team == "EZX Team Summary":
    st.subheader("📊 Overall Productivity Across Teams")

    # **Extract the Required Data**
    df_weekly_summary = df_weekly[["Team Name"] + week_columns + av_week_columns]

    # Group by team name and sum across all weeks
    df_team_weekly_total = df_weekly_summary.groupby("Team Name").sum()

    # Calculate overall productivity for each team
    overall_productivity = {
        team: (df_team_weekly_total.loc[team, week_columns].sum() /
               df_team_weekly_total.loc[team, av_week_columns].sum()) * 100
        for team in df_team_weekly_total.index
    }

    # Convert to DataFrame for plotting
    df_overall_productivity = pd.DataFrame(overall_productivity.items(), columns=["Team", "Productivity (%)"])

    # **Create an Interactive Bar Chart**
    fig_overall = go.Figure()

    fig_overall.add_trace(go.Bar(
        x=df_overall_productivity["Team"],
        y=df_overall_productivity["Productivity (%)"],
        text=df_overall_productivity["Productivity (%)"].apply(lambda x: f"{x:.1f}%"),
        textposition='auto',
        marker=dict(color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]),  # Custom team colors
    ))

    # **Add 75% Dotted Target Line**
    fig_overall.add_shape(
        type="line",
        x0=df_overall_productivity["Team"].iloc[0],  # Start from first team
        x1=df_overall_productivity["Team"].iloc[-1],  # End at last team
        y0=75,
        y1=75,
        line=dict(color="red", width=2, dash="dot"),  # Red dotted line for 75% target
    )

    # **Add Annotation for Target Line**
    fig_overall.add_annotation(
        x=df_overall_productivity["Team"].iloc[-1],  # Position at the last team
        y=75,
        text="🎯 Target: 75%",
        showarrow=False,
        font=dict(size=12, color="red"),
        bgcolor="white",
    )

    # Customize layout
    fig_overall.update_layout(
        xaxis_title="Team",
        yaxis_title="Overall Productivity (%)",
        yaxis=dict(range=[0, 100], showgrid=True, gridcolor="lightgray"),  # Ensure y-axis goes up to 100%
        xaxis=dict(tickangle=-45),
        template="plotly_white",
        showlegend=False
    )

    # **Show Chart in Streamlit**
    st.plotly_chart(fig_overall, use_container_width=True)

# **Overall EZX Team Productivity Chart (Only in "EZX Team Summary" Page)**
if selected_team == "EZX Team Summary":
    st.subheader("🌍 Overall EZX Team Productivity")

    # **Summing up all teams together**
    total_work_hours = df_team_weekly_total[week_columns].sum().sum()
    total_available_hours = df_team_weekly_total[av_week_columns].sum().sum()

    # **Calculate Overall EZX Productivity (%)**
    ezx_productivity = (total_work_hours / total_available_hours) * 100 if total_available_hours else 0

    # **Create a Single Bar Graph for Overall EZX Team**
    fig_ezx = go.Figure()

    fig_ezx.add_trace(go.Bar(
        x=["EZX Team"],
        y=[ezx_productivity],
        text=[f"{ezx_productivity:.1f}%"],
        textposition='auto',
        marker=dict(color="#1f77b4")  # Single color for EZX Team
    ))

    # **Customize Layout**
    fig_ezx.update_layout(
        yaxis_title="Overall Productivity (%)",
        yaxis=dict(range=[0, 100], showgrid=True, gridcolor="lightgray"),
        template="plotly_white",
        showlegend=False
    )

    # **Show Chart in Streamlit**
    st.plotly_chart(fig_ezx, use_container_width=True)

# **Overall Productivity for the Selected Team (Only in Their Respective Pages)**
if selected_team in team_names and selected_team != "EZX Team Summary":
    st.subheader(f"🌍 Overall {selected_team} Productivity")

    # **Extract Data for Selected Team**
    df_selected_team = df_weekly[df_weekly["Team Name"].str.contains(selected_team, case=False, na=False)]

    # Sum across all weeks for the team
    total_team_work_hours = df_selected_team[week_columns].sum().sum()
    total_team_available_hours = df_selected_team[av_week_columns].sum().sum()

    # **Calculate Overall Team Productivity (%)**
    team_productivity = (total_team_work_hours / total_team_available_hours) * 100 if total_team_available_hours else 0

    # **Create a Single Bar Graph for the Selected Team**
    fig_team = go.Figure()

    fig_team.add_trace(go.Bar(
        x=[selected_team],
        y=[team_productivity],
        text=[f"{team_productivity:.1f}%"],
        textposition='auto',
        marker=dict(color="#1f77b4")  # Single color for each team
    ))

    # **Customize Layout**
    fig_team.update_layout(
        yaxis_title="Overall Productivity (%)",
        yaxis=dict(range=[0, 100], showgrid=True, gridcolor="lightgray"),
        template="plotly_white",
        showlegend=False
    )

    # **Show Chart in Streamlit**
    st.plotly_chart(fig_team, use_container_width=True)

import plotly.express as px

# **Function to Get Work Distribution Data**
def get_work_distribution():
    # Load Master Data
    df_master = data["Master Data"]

    # Remove "Time Off" records
    df_filtered = df_master[df_master["Product/Service"] != "Time off"]

    # Aggregate total hours spent per Product/Service
    df_distribution = df_filtered.groupby("Product/Service")["Duration"].sum().reset_index()

    # Calculate Total Hours Worked
    total_hours = df_distribution["Duration"].sum()

    # Normalize Values as Percentage
    df_distribution["Percentage"] = (df_distribution["Duration"] / total_hours) * 100

    return df_distribution

# **Show Work Distribution Only in EZX Team Summary**
if selected_team == "EZX Team Summary":
    st.subheader("📊 Work Distribution Across Product/Services")

    # Fetch Work Distribution Data
    df_work_distribution = get_work_distribution()

    # **Create Bar Chart**
    fig_work_distribution = px.bar(
        df_work_distribution,
        x="Product/Service",
        y="Duration",
        text=df_work_distribution["Percentage"].apply(lambda x: f"{x:.1f}%"),  # Show % on bars
        labels={"Duration": "Total Hours"},
        title="Workload Distribution by Product/Service",
        color="Product/Service",  # Different colors for categories
        color_discrete_sequence=px.colors.qualitative.Set3  # Use custom color palette
    )

    # **Customize Layout**
    fig_work_distribution.update_layout(
        xaxis_title="Product/Service",
        yaxis_title="Total Hours",
        xaxis=dict(tickangle=-45),  # Rotate labels for readability
        yaxis=dict(showgrid=True, gridcolor="lightgray"),
        template="plotly_white",
        showlegend=False
    )

    # **Show Chart in Streamlit**
    st.plotly_chart(fig_work_distribution, use_container_width=True)


    # **Function to Get Work Distribution for a Selected Team**
    def get_team_work_distribution(team_name):
        # Load Master Data
        df_master = data["Master Data"]

        # Filter for the Selected Team
        df_filtered = df_master[df_master["Team Name"].str.contains(team_name, case=False, na=False)]

        if df_filtered.empty:
            return None  # Return None if no data found

        # Summing Up the Duration for Each Product/Service
        df_distribution = df_filtered.groupby("Product/Service")["Duration"].sum().reset_index()

        # Sort Data in Descending Order
        df_distribution = df_distribution.sort_values(by="Duration", ascending=False)

        return df_distribution


    # **Generate Work Distribution Chart for Individual Teams**
    if selected_team in team_names and selected_team != "EZX Team Summary":
        st.subheader(f"📊 Work Distribution for {selected_team}")

        # Fetch Work Distribution Data
        df_team_distribution = get_team_work_distribution(selected_team)

        if df_team_distribution is not None:
            # **Create a Horizontal Bar Chart**
            fig_distribution = go.Figure()

            fig_distribution.add_trace(go.Bar(
                y=df_team_distribution["Product/Service"],
                x=df_team_distribution["Duration"],
                text=df_team_distribution["Duration"],
                textposition='auto',
                orientation='h',  # Horizontal Bar Chart
                marker=dict(color="royalblue")  # Custom Color
            ))

            # **Customize Layout**
            fig_distribution.update_layout(
                xaxis_title="Total Hours",
                yaxis_title="Product/Service",
                title=f"Work Distribution Across Product/Services for {selected_team}",
                template="plotly_white"
            )

            # **Show Chart in Streamlit**
            st.plotly_chart(fig_distribution, use_container_width=True)

        else:
            st.warning(f"No work distribution data found for {selected_team}.")

# **Function to Get the Top Performer Based on "Projects" Work Percentage**
def get_top_project_performer(team_name):
    # Load Master Data
    df_master = data["Master Data"]

    # Filter for the Selected Team
    df_filtered = df_master[df_master["Team Name"].str.contains(team_name, case=False, na=False)]

    if df_filtered.empty:
        return None  # Return None if no data found

    # Further Filter for Only "Projects" Work
    df_projects = df_filtered[df_filtered["Product/Service"] == "Projects"]

    if df_projects.empty:
        return None  # No "Projects" work recorded for this team

    # Load Weekly Summary to Get "Available Hours" (40 - Time Off)
    df_weekly = data["Weekly Summary"]
    df_team_weekly = df_weekly[df_weekly["Team Name"].str.contains(team_name, case=False, na=False)]

    # Summing Up the "Projects" Duration for Each Employee
    df_performer = df_projects.groupby("Employee Name")["Duration"].sum().reset_index()

    # Get Each Employee's Available Hours (40 - Time Off)
    df_availability = df_team_weekly[["Employee Name"] + [col for col in df_team_weekly.columns if col.startswith("Av Week ")]]

    # Calculate Total Available Hours for Each Employee
    df_availability["Total Available Hours"] = df_availability.iloc[:, 1:].sum(axis=1)

    # Merge the Data
    df_performer = df_performer.merge(df_availability[["Employee Name", "Total Available Hours"]], on="Employee Name", how="left")

    # **Calculate "Projects Work Percentage"**
    df_performer["Projects Work %"] = (df_performer["Duration"] / df_performer["Total Available Hours"]) * 100

    # Identify the **Top Performer** (Highest "Projects Work %" Score)
    df_performer = df_performer.dropna().sort_values(by="Projects Work %", ascending=False)

    if df_performer.empty:
        return None  # Return None if no valid data found

    top_performer = df_performer.iloc[0]  # Pick the Top Employee

    return top_performer

# **Display Top Performer in the Selected Team Based on "Projects Work %"**
if selected_team in team_names and selected_team != "EZX Team Summary":
    top_performer = get_top_project_performer(selected_team)

    if top_performer is not None:
        st.success(f"🏆 **Top Performer in {selected_team}:** {top_performer['Employee Name']} with **{top_performer['Projects Work %']:.1f}%** efficiency in Projects!")
    else:
        st.warning(f"No 'Projects' work data found to determine the top performer in {selected_team}.")

# **Dropdown to Select Employee (Only in Team Pages)**
if selected_team in team_names and selected_team != "EZX Team Summary":
    st.subheader(f"📊 Work Distribution for {selected_team}")

    # Fetch Employee List for the Selected Team
    df_team_members = data["Master Data"][data["Master Data"]["Team Name"].str.contains(selected_team, case=False, na=False)]
    employee_list = df_team_members["Employee Name"].unique()

    selected_employee = st.selectbox("Select an Employee:", employee_list, index=0)

    # **Function to Calculate Work Distribution for Selected Employee**
    def get_employee_work_distribution(employee_name):
        df_master = data["Master Data"]

        # Filter data for the selected employee
        df_employee = df_master[df_master["Employee Name"] == employee_name]

        if df_employee.empty:
            return None  # Return None if no data found

        # Load Weekly Summary to Get Available Hours (40 - Time Off)
        df_weekly = data["Weekly Summary"]
        df_employee_weeks = df_weekly[df_weekly["Employee Name"] == employee_name]

        if df_employee_weeks.empty:
            return None  # No weekly summary data found

        # **Sum Up Total Available Hours (40 - Time Off) Across All Weeks**
        total_available_hours = df_employee_weeks[[col for col in df_employee_weeks.columns if col.startswith("Av Week ")]].sum().sum()

        if total_available_hours <= 0:
            return None  # No available hours left (possibly full time-off)

        # **Summing Up Duration spent on each Product/Service**
        df_distribution = df_employee[df_employee["Product/Service"] != "Time off"].groupby("Product/Service")["Duration"].sum().reset_index()

        # **Calculate Work Distribution as Percentage of Available Hours**
        df_distribution["Percentage"] = (df_distribution["Duration"] / total_available_hours) * 100

        # **Ensure percentages do not exceed 100%**
        df_distribution["Percentage"] = df_distribution["Percentage"].apply(lambda x: min(x, 100))

        # **Sort Data in Descending Order**
        df_distribution = df_distribution.sort_values(by="Percentage", ascending=False)

        return df_distribution

    # **Fetch Work Distribution for Selected Employee**
    df_employee_distribution = get_employee_work_distribution(selected_employee)

    if df_employee_distribution is not None:
        # **Create a Horizontal Bar Chart**
        fig_employee_distribution = go.Figure()

        fig_employee_distribution.add_trace(go.Bar(
            y=df_employee_distribution["Product/Service"],
            x=df_employee_distribution["Percentage"],
            text=df_employee_distribution["Percentage"].apply(lambda x: f"{x:.1f}%"),
            textposition='auto',
            orientation='h',  # Horizontal Bar Chart
            marker=dict(color="royalblue")  # Custom Color
        ))

        # **Customize Layout**
        fig_employee_distribution.update_layout(
            xaxis_title="Percentage of Work Distribution",
            yaxis_title="Product/Service",
            title=f"Work Distribution for {selected_employee}",
            template="plotly_white",
            xaxis=dict(range=[0, 100])  # Ensuring the maximum percentage is 100%
        )

        # **Show Chart in Streamlit**
        st.plotly_chart(fig_employee_distribution, use_container_width=True)

    else:
        st.warning(f"No work distribution data found for {selected_employee} or available hours are 0.")

# **Function to Get Employees' Projects % and Sort in Descending Order**
def get_sorted_team_performance(team_name):
    # Load Master Data
    df_master = data["Master Data"]

    # Filter for the Selected Team
    df_team = df_master[df_master["Team Name"].str.contains(team_name, case=False, na=False)]

    if df_team.empty:
        return None  # No data found

    # Load Weekly Summary to Get Available Hours (40 - Time Off)
    df_weekly = data["Weekly Summary"]
    df_team_weekly = df_weekly[df_weekly["Team Name"].str.contains(team_name, case=False, na=False)]

    if df_team_weekly.empty:
        return None  # No weekly summary data

    # Summing Up Total Available Hours (40 - Time Off) Across All Weeks
    df_team_weekly["Total Available Hours"] = df_team_weekly[[col for col in df_team_weekly.columns if col.startswith("Av Week ")]].sum(axis=1)

    # Summing Up Total Projects Duration per Employee
    df_projects = df_team[df_team["Product/Service"] == "Projects"]
    df_projects_summary = df_projects.groupby("Employee Name")["Duration"].sum().reset_index()

    # Merge with Available Hours Data
    df_performance = df_projects_summary.merge(df_team_weekly[["Employee Name", "Total Available Hours"]], on="Employee Name", how="left")

    # Calculate Projects % (Projects Duration / Available Hours) * 100
    df_performance["Projects %"] = (df_performance["Duration"] / df_performance["Total Available Hours"]) * 100

    # Handle Missing Data and Sort
    df_performance = df_performance.dropna().sort_values(by="Projects %", ascending=False)

    return df_performance

# **Generate Sorted Chart for Each Team**
if selected_team in team_names and selected_team != "EZX Team Summary":
    st.subheader(f"📊 Employee Performance in {selected_team} (Sorted by Projects %)")


    # Fetch Sorted Performance Data
    df_sorted_performance = get_sorted_team_performance(selected_team)

    if df_sorted_performance is not None and not df_sorted_performance.empty:
        # **Create a Horizontal Bar Chart**
        fig_sorted_performance = go.Figure()

        fig_sorted_performance.add_trace(go.Bar(
            y=df_sorted_performance["Employee Name"],
            x=df_sorted_performance["Projects %"],
            text=df_sorted_performance["Projects %"].apply(lambda x: f"{x:.1f}%"),
            textposition='auto',
            orientation='h',  # Horizontal Bar Chart
            marker=dict(color="royalblue")  # Custom Color
        ))

        # **Customize Layout**
        fig_sorted_performance.update_layout(
            xaxis_title="Projects %",
            yaxis_title="Employee",
            title=f"Sorted Employee Performance in {selected_team}",
            template="plotly_white",
            xaxis=dict(range=[0, 100])  # Ensuring the maximum percentage is 100%
        )

        # **Show Chart in Streamlit**
        st.plotly_chart(fig_sorted_performance, use_container_width=True)

    else:
        st.warning(f"No projects work data found for {selected_team}.")

if selected_team == "📊 Data Check":
    st.subheader("⚠ Employees with Less than 40 Hours in Any Week")

    # Load Master Data
    df_master = data["Master Data"]

    # Ensure "Activity Date" is converted to datetime format
    df_master["Activity Date"] = pd.to_datetime(df_master["Activity Date"], format="%d-%m-%Y", errors='coerce')

    # **Calculate Week Number for Each Entry**
    df_master["Week Number"] = df_master["Activity Date"].dt.isocalendar().week

    # **Get Unique List of Employees and Weeks**
    all_employees = df_master["Employee Name"].unique()
    all_weeks = df_master["Week Number"].unique()

    # **Create a Complete Grid of Employees x Weeks**
    import itertools
    all_combinations = pd.DataFrame(itertools.product(all_employees, all_weeks), columns=["Employee Name", "Week Number"])

    # **Group by Employee and Week Number to get total worked hours**
    df_weekly_hours = df_master.groupby(["Employee Name", "Week Number"])["Duration"].sum().reset_index()

    # **Merge to Ensure Every Employee-Week Exists**
    df_complete = all_combinations.merge(df_weekly_hours, on=["Employee Name", "Week Number"], how="left").fillna(0)

    # **Calculate Missing Hours**
    df_complete["Missing Hours"] = 40 - df_complete["Duration"]

    # **Filter employees who worked less than 40 hours in any week**
    df_missing_hours = df_complete[df_complete["Missing Hours"] > 0].copy()

    # Merge with Team Name for better visibility
    df_missing_hours = df_missing_hours.merge(df_master[["Employee Name", "Team Name"]].drop_duplicates(),
                                              on="Employee Name", how="left")

    # **Show Only Relevant Columns**
    df_missing_hours = df_missing_hours[["Employee Name", "Team Name", "Week Number", "Duration", "Missing Hours"]]

    # **Display Results**
    if not df_missing_hours.empty:
        st.warning("🚨 The following employees did not complete 40 hours in one or more weeks:")
        st.dataframe(df_missing_hours, use_container_width=True)
    else:
        st.success("✅ All employees have at least 40 hours per week from Week 1 until now.")