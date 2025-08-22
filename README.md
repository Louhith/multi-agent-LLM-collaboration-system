# Multi-LLM Collaboration Agent

An intelligent agent system that uses multiple specialized LLMs to collaboratively handle complex research and scheduling tasks.

## Features

* **Dual-Scenario Implementation**: Demonstrates both a research-collaboration task (Scenario 1) and a schedule-optimization task (Scenario 2).
* **Modular Architecture**: Code is factored into separate files for agents (`agents.py`), core logic (`orchestrator.py`), external tools (`tools.py`), and execution (`main.py`).
* **Multi-Agent System**: Utilizes specialized agents (e.g., ResearchBot, ActionItemExtractor) for distinct subtasks.
* **Iterative Improvement**: Scenario 1 features a Moderator agent that reviews work over multiple rounds, providing feedback for refinement.
* **Tool Integration**: Scenario 2 demonstrates how AI agents can interact with placeholder "tools" to perform actions like scheduling calendar events.
* **Test-Driven Design**: Includes a deterministic `FakeLLM` mode for rapid, reliable unit testing of the core application logic.
* **Persistent History**: Agent contributions for each scenario are logged to dedicated SQLite databases (`research_history.db`, `schedule_history.db`).

## How to Run

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git)
    cd YOUR_REPOSITORY_NAME
    ```

2.  **Set up the Environment**
    ```bash
    # Create and activate a virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

    # Install dependencies
    pip install -r requirements.txt
    ```
    *Note: For the visualization feature, you must also install the Graphviz system software from [graphviz.org/download/](https://graphviz.org/download/) and ensure it is added to your system's PATH.*

3.  **Run the Project**
    ```bash
    # This will run the automated tests and then both scenario demonstrations.
    python main.py
    ```

## Design Choices

* **Orchestrator Pattern**: A central `Orchestrator` manages the workflow, which is a clean and scalable way to control a multi-agent system. This engine is flexible and was reused for both distinct scenarios.
* **Dual-Backend System (`FakeLLM` vs. `HuggingFaceAgent`)**: Separating the deterministic mock from the live AI allowed for fast unit testing of the application's logic, a key practice for building robust systems.
* **Tool Separation**: External API interactions (even simulated ones) are kept in `tools.py` to decouple them from the core AI logic, making the system easier to maintain and extend.