export DAGSTER_HOME := `pwd` + "/.dagster"
dagster_config_path := DAGSTER_HOME + "/dagster.yaml"
dagster_is_configured := path_exists(dagster_config_path)

_init_dagster:
	mkdir -p .dagster
	echo "telemetry:" > {{ dagster_config_path }}
	echo "  enabled: false" >> {{ dagster_config_path }}
	echo "*" >> {{ DAGSTER_HOME }}/.gitignore

# run dagster development instance
run:
	{{ if dagster_is_configured == "false" { "just _init_dagster" } else { "" } }}
	poetry run dagster dev

kernel:
    poetry run ipython kernel install --user --name=.venv

dummy:
	poetry run python scripts/gen_dummy_data.py

simulate:
	poetry run python scripts/data_simulation.py

# remove Python file artifacts
clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +


tm:
	poetry run python tests/test_teacher_model.py

design:
	poetry run python experiment/design/_designer.py


app:
	poetry run streamlit run experiment/app/main.py

mlflow:
	./scripts/run_mlflow.sh
