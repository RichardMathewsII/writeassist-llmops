import streamlit as st
import os
import json
import pandas as pd


st.set_page_config(layout="wide")

# Set the path to the artifacts folder
folder_path = "./best_artifacts/"

# Get all second level folders in the given folder path
dagster_ids = [f.path.split('/')[-1] for f in os.scandir(folder_path) if f.is_dir()]
run_names = {}
run_configs = {}
for dagster_id in dagster_ids:
    run_config_filepath = os.path.join(folder_path, dagster_id, "run_configuration.json")
    if not os.path.exists(run_config_filepath):
        run_configs[dagster_id] = {}
        run_names[dagster_id] = None
        continue
    with open(run_config_filepath) as file:
        run_configs[dagster_id] = json.load(file)
    
    run_names[dagster_id] = run_configs[dagster_id]["resources"]["tracking_client"]["config"]["run_name"]

# Display a dropdown to select the second level folder
selected_run = st.selectbox("Select a dagster run", dagster_ids, format_func=lambda x: run_names[x])
st.session_state.run_ids = dagster_ids
st.session_state.run_id = selected_run
st.session_state.run_configs = run_configs
st.session_state.run_names = run_names

# iterate over each dagster run id folder, get the run_configuration.json, extract the fields and render them in a container, with the option to select the artifact
if not selected_run:
    st.warning("No dagster runs found in the selected folder.")

cols = st.columns(2)
with cols[0]:
    st.header("Run configuration")
    st.json(run_configs[selected_run])

with cols[1]:
    st.header("Artifacts")

    # Get all folders in the run id folder
    run_id_folder = os.path.join(folder_path, selected_run)
    artifact_folders = [f.path.split('/')[-1] for f in os.scandir(run_id_folder) if f.is_dir()]
    selected_asset_key = st.selectbox("Select an asset key", artifact_folders)
    # get every file in the selected asset key folder
    artifacts = [f.path.split('/')[-1] for f in os.scandir(os.path.join(run_id_folder, selected_asset_key)) if f.is_file()]
    selected_artifact = st.selectbox("Select an artifact", artifacts)
    if selected_artifact.endswith(".json"):
        with open(os.path.join(run_id_folder, selected_asset_key, selected_artifact)) as file:
            data = json.load(file)
    elif selected_artifact.endswith(".csv"):
        data = pd.read_csv(os.path.join(run_id_folder, selected_asset_key, selected_artifact))
    elif selected_artifact.endswith(".parquet"):
        data = pd.read_parquet(os.path.join(run_id_folder, selected_asset_key, selected_artifact))
    else:
        data = None


    # select which position in the json file to show
    if isinstance(data, list):
        selected_position = st.selectbox("Select an item", list(range(len(data))))

        st.json(data[selected_position])
    elif isinstance(data, pd.DataFrame):
        cols = st.multiselect("Select columns to display", data.columns)
        st.dataframe(data[cols])
    else:
        st.json(data)
