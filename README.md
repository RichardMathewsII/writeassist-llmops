# Experimentation Repository
> This repo houses all methodology and system experiments, covering topics such as LLMs, embeddings, RAG, and prompt engineering.

## Usage
* To understand how to best configure our software to create value for the target user
* Understand performance tradeoffs
* Explore methodologies to be implemented in the cloud-based software solution

## Get Started
* The `notebooks/` folder will contain your notebooks for rapid prototyping
* The `scripts/` folder will contain testing scripts
* The `experiment/` folder is our python package for experimentation. It contains the dagster pipelines.

### Prerequisites
* Poetry (*required*) - follow these [instructions](https://python-poetry.org/docs/#installing-with-the-official-installer) to install poetry
* Just (*required*) - install [here](https://just.systems/man/en/chapter_4.html) using your system's package manager (e.g. homebrew for macOS, chocolatey for windows). This will be helpful for automating common CLI commands.
* .env file (*required*) - in the root of the repo, create a `.env` file. This .env file is available in our slack channel in one of the pinned posts, use the latest version.


### Install
* Install the poetry environment, in bash, navigate to this directory, and run `poetry install`. Your environment should appear as a .venv. To run python files under this environment, run `poetry run python <python file>` or activate a shell with `poetry shell`.
* Install the environment as a jupyter kernel to work with your notebooks by running
  * `just kernel` (with just)
  * `poetry run ipython kernel install --user --name=.venv`

### Run dagster server
In the root directory of the repo, run `just run`.

## System Design
### Requirements
- Consume a set of data inputs, transform them, and create feedback predictions mapped to the inputs. Basically do inference in batch.
- The actual inference system is agnostic to evaluation. There should be an evaluation system wrapped around it, feeding inputs that are paired with some ground truth.
- The inference system takes a set of data inputs, and we may manually define those or draw upon simulated inputs from the evaluation
- Inference can be run independent of evaluation, but not vice versa
- The user data asset group is known data, we can use this in the system for anything we want. None of it is considered "holdout". Any holdout should be in an isolation evaluation group.
- The system should be stateless. One run of the pipeline does not affect future runs. Any dynamics (e.g. teacher model) should be simulated within a single run.
- There should be extensive logging for complete transparency and qualitative review
- Pipeline should be configuration-based. It should be possible to turn off an input (turn off class documents, essay context, RAG, etc.), to modify the behavior of aprocess (teacher model building, RAG, etc.).

### Configuration
Principles

- **Resource**. If you want a configuration parameter shared across all assets but modifiable via the launchpad, define it in a shared resource with a default value
- **Environment**. If you want a configuration parameter shared across all assets but inherited from the compute environment (cloud cluster, local user, etc.), define it as an `EnvVar` in the `Definitions` (see example below).
- **Asset**. If you want a configuration parameter modifiable at the asset/op level, define it as a `Config` and pass to the asset/op as an argument. You can pass the config to multiple assets, but then at launch time you can change individually for each asset/op.

---

**Resource Configurations**
- Embedding model and it's hyperparameters
  - We want to use the same embedding model for the vector store as we do for processing user query in RAG setup
- LLM and it's hyperparameters
  - It's more likely we test a single LLM against all tasks then we test one LLM on one task and a different one on another in a single run
- Teacher model
  - The teacher model is not task-specific, therefore does not make sense to configure at the asset-level

**Environment Variables**
- Personal access metadata for AWS resources
  - Specific to the user in their local setup

**Asset Configuration**
- User data source
  - The source of data may change for each type of data depending on availability
- User inputs
  - Each user input type will have a different structure
- Retrieval approach
  - Might have different approaches depending on the task
- Prompting technique
  - Might have different approaches depending on the task

### Pipeline Design
- Asset groups are seperated based on the binary [task specific, not task specific]
  - We want to support jobs that run a task on its own, and thus can run only the assets for that task as well as the task-agnostic assets that the task is dependent on.
- Operations like RAG, prompting, and LLM querying are contained in task-specific asset groups rather than in their own generic asset groups
  - These operations are inherent to a task, thus we must decouple task jobs and thus decouple these operations at the task level.
  - e.g. If I have a generic LLM asset that processes a prompt and returns a response, that LLM asset would then consume from all task specific prompts, thereby creating a coupling amongst the task pipelines.