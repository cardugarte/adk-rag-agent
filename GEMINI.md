# Project Overview

This project implements a Retrieval Augmented Generation (RAG) agent using the Google Agent Development Kit (ADK) and Google Cloud Vertex AI. The agent is specialized in legal contract analysis, editing, and generation, with a Spanish-language interface.

## Key Technologies

*   **Backend:** Python
*   **AI/ML:** Google Agent Development Kit (ADK), Google Cloud Vertex AI, Gemini 2.5 Flash
*   **Google Cloud Services:** Vertex AI, Cloud Storage, Secret Manager
*   **Dependencies:** `google-adk`, `google-cloud-aiplatform`, `google-genai`, `google-cloud-storage`, `google-cloud-secret-manager`, `google-api-python-client`, `authlib`, `google-auth`, `google-auth-httplib2`, `python-dotenv`, `pydantic`, `requests`, `PyYAML`

## Architecture

The project is structured as a Python application with the following key components:

*   **`asistent/agent.py`:** The main entry point of the agent, defining its name, model, description, tools, and instruction prompt.
*   **`asistent/tools/`:** A directory containing the implementation of the agent's tools, which are responsible for interacting with the Vertex AI RAG service. Each tool is a separate Python file (e.g., `rag_query.py`, `create_corpus.py`).
*   **`requirements.txt`:**  Specifies the Python dependencies for the project.
*   **`README.md`:** Provides a detailed overview of the project, including setup instructions, usage, and troubleshooting.

# Building and Running

## Prerequisites

*   A Google Cloud account with billing enabled
*   A Google Cloud project with the Vertex AI API enabled
*   Appropriate access to create and manage Vertex AI resources
*   Python 3.9+ environment

## Setup and Installation

1.  **Set up Google Cloud Authentication:**
    *   Install the Google Cloud CLI: [https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)
    *   Initialize the gcloud CLI: `gcloud init`
    *   Set up Application Default Credentials: `gcloud auth application-default login`

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Agent

The `README.md` file does not specify how to run the agent. However, based on the project structure and the use of the ADK, it is likely that the agent is run using the `adk` command-line tool.

**TODO:** Add instructions on how to run the agent once the exact command is known.

# Development Conventions

*   **Coding Style:** The code follows standard Python conventions (PEP 8).
*   **Testing:** There are no tests included in the project.
*   **Contribution Guidelines:** There are no contribution guidelines specified.
