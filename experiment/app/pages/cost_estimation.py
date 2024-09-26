import streamlit as st
import os
import json
import pandas as pd


st.set_page_config(layout="wide")

# Set the path to the artifacts folder
data = pd.DataFrame()
for run_id in st.session_state.run_ids:
    cost_estimation_folder = f"artifacts/{run_id}/llm/cost_estimations/"
    if not os.path.exists(cost_estimation_folder):
        continue

    # load each json file from cost_estimation_folder
    for file in os.listdir(cost_estimation_folder):
        with open(os.path.join(cost_estimation_folder, file), 'r') as f:
            data_add = pd.DataFrame(json.load(f), index=[file])
    
            data = pd.concat([data, data_add])

tabs = st.tabs(["Individual Call Costs", "Aggregate Costs"])

with tabs[0]:
    dagster_run_id_filter = st.selectbox("Filter by run_id", data["run_id"].unique(), format_func=lambda x: st.session_state.run_names[x])
    cols = st.columns(2)
    with cols[0]:
        st.header("Total Costs Per Run")
        st.dataframe(data.loc[data.run_id == dagster_run_id_filter].drop(columns=['run_id']))
    
    with cols[1]:
        st.header("Run configuration")
        st.json(st.session_state.run_configs.get(dagster_run_id_filter, {}))

with tabs[1]:
    total_cost = data['total_cost'].sum()
    st.metric("Total Cost", total_cost)
    st.dataframe(data.groupby("run_id").sum().drop(columns=['mock_response', "model"]))
