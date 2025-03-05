import streamlit as st
import pandas as pd

# Title for Analytics Page
st.title("Workload Distribution - Analytics")

# Check if session state contains data
if "df_additional" in st.session_state and "df_merged" in st.session_state:
    df_additional = st.session_state["df_additional"]
    df_merged = st.session_state["df_merged"]

    # Ensure data is available
    if df_additional is None or df_merged is None:
        st.warning("⚠️ Required data is missing. Please upload files and process the data on the main page first.")
    else:
        st.subheader("Step 8: Run Analytics and Compare Budget")

        # Convert numeric columns to float for calculation
        df_merged["USD per Hour"] = pd.to_numeric(df_merged["USD per Hour"], errors='coerce').fillna(0)
        df_merged["Duration"] = pd.to_numeric(df_merged["Duration"], errors='coerce').fillna(0)
        df_additional["Amount"] = pd.to_numeric(df_additional["Amount"], errors='coerce').fillna(0)

        # Create an empty results table
        results = []

        # Loop through each unique 'Num' in df_additional
        for index, row in df_additional.iterrows():
            num_value = row["Num"]  # Extract unique Num value
            amount_budget = row["Amount"]  # Extract budgeted amount
            project_manager = row["Project Manager"]  # Extract Project Manager

            # Find matching rows in Master Data where 'Client' contains the 'Num' value
            matching_rows = df_merged[df_merged["Client"].astype(str).str.contains(str(num_value), na=False)]

            # Extract Client Information
            clients = matching_rows["Client"].unique().tolist()
            client_list = ", ".join(clients) if clients else "N/A"

            # Perform the calculation: Duration * USD per Hour
            matching_rows["Calculated Cost"] = matching_rows["Duration"] * matching_rows["USD per Hour"]
            total_cost = matching_rows["Calculated Cost"].sum()

            # Determine if the budget is exceeded
            budget_status = "Exceeded" if total_cost > amount_budget else "Within Budget"

            # Store results
            results.append({
                "Num": num_value,
                "Client": client_list,
                "Project Manager": project_manager,
                "Total Calculated Cost": total_cost,
                "Budgeted Amount": amount_budget,
                "Status": budget_status
            })

        # Convert results into a DataFrame
        df_results = pd.DataFrame(results)

        # Display Results Table
        st.subheader("Comparison of Budget and Actual Cost")
        st.dataframe(df_results)

        # Save the results for download
        output_file = "Budget_Comparison.xlsx"
        with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
            df_results.to_excel(writer, sheet_name="Budget Comparison", index=False)

        # Download Button
        with open(output_file, "rb") as f:
            st.download_button("Download Budget Comparison", f, "Budget_Comparison.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

else:
    st.warning("⚠️ Final Cleaned Additional Data or Master Data is not available. Please upload and process the data first on the main page.")
