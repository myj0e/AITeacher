# Personalized Learning App

## Description

The Personalized Learning App is a command-line application designed to help users learn new topics by dynamically generating a knowledge graph and guiding them through interactive learning sessions. It leverages Language Models (LLMs) – currently simulated – to break down complex learning goals into manageable knowledge points, provide explanations and examples, and test user understanding. The app tracks user mastery and saves progress, allowing for a personalized learning experience.

## Features

*   **Knowledge Graph Generation:** (Simulated) Takes a user's learning goal and breaks it down into a structured list of knowledge points.
*   **Relationship Mapping:** (Simulated) Establishes prerequisite and postrequisite relationships between knowledge points.
*   **Interactive Learning Loop:** Guides the user through each knowledge point sequentially.
*   **Concept Explanations:** Provides explanations for each knowledge point (currently placeholder text).
*   **Practical Examples:** Offers examples to illustrate concepts (currently placeholder text).
*   **Testing and Assessment:** Presents questions (multiple-choice, short answer) to test understanding (using placeholder questions and basic evaluation).
*   **Progress Tracking:** Monitors user mastery levels for each knowledge point.
*   **Data Persistence:** Saves the generated knowledge graph and user progress to local JSON files (`data/` directory).
*   **Command-Line Interface:** All interactions occur through a CLI.

## How it Works (High-Level)

1.  **User Input:** The user provides a learning goal (e.g., "learn Python basics").
2.  **Knowledge Graph Creation (Simulated):** The application (simulating LLM interaction) breaks down the learning goal into a series of interconnected `KnowledgePoint` objects. These points include prompts for explanations, examples, and tests.
3.  **Learning Path Presentation:** The app displays the generated learning path to the user.
4.  **Iterative Learning:** The user proceeds topic by topic. For each topic:
    *   They receive an explanation.
    *   They can view an example.
    *   They are tested on the material.
5.  **Mastery & Progress:** The app evaluates their test performance against a mastery threshold for the topic and saves their progress.
6.  **Prerequisite Handling:** The app checks for prerequisite mastery before starting a new topic (basic implementation).

## Setup and Installation

**Prerequisites:**
*   Python 3.7 or higher.

**Installation:**
1.  **Clone the Repository:**
    ```bash
    git clone <repository_url> # Replace <repository_url> with the actual URL
    cd personalized-learning-app # Or your chosen directory name
    ```
2.  **Install Dependencies:**
    The primary external dependency is Pydantic.
    ```bash
    pip install pydantic
    ```
    (If a `requirements.txt` file is available in the future, you would use `pip install -r requirements.txt`)

## Running the Application

Navigate to the application's root directory (e.g., `personalized-learning-app`) in your terminal. Run the main script using:

```bash
python learning_app/main.py
```
Or, if you are already in the `learning_app` directory:
```bash
python main.py
```

The application will then guide you through the process, starting with loading any existing data or asking for your learning goal.

## LLM Configuration (Important Note)

**The current version of this application uses placeholder/simulated LLM responses.** It does **not** make live calls to any external LLM APIs.

The logic for generating content (knowledge graphs, explanations, examples, test questions) is hardcoded or uses simple string formatting based on predefined prompts.

To integrate a real LLM:
1.  You would need to have an API key and access to an LLM provider (e.g., OpenAI, Anthropic, etc.).
2.  Modify the file `learning_app/core/llm_interaction.py`.
3.  Update the placeholder variables `LLM_API_ENDPOINT` and `LLM_API_KEY` with your actual LLM API details.
4.  Implement the actual API call logic within the functions in that file. The existing `TODO` comments in `generate_knowledge_graph` and `get_relationships` provide detailed outlines of how these API calls might be structured.
5.  Similarly, the functions in `learning_app/core/learning_flow.py` (`get_concept_explanation`, `get_example`, `get_test_questions`) currently return placeholder content. These would need to be updated to use the `KnowledgePoint`'s specific prompts and make calls to an LLM via the `llm_interaction.py` module or a dedicated `LLMProvider` class.

## Project Structure

*   `learning_app/`: Main application package.
    *   `main.py`: Entry point of the application, handles the main learning loop and CLI.
    *   `core/`: Core logic and data structures.
        *   `data_structures.py`: Defines Pydantic models (`KnowledgePoint`, `UserProgress`).
        *   `llm_interaction.py`: (Simulated) Handles generation of knowledge graphs and relationships. Placeholder for real LLM calls.
        *   `learning_flow.py`: Manages content delivery (explanations, examples, tests) and answer evaluation.
        *   `persistence.py`: Handles saving and loading data (knowledge graph, user progress) to/from JSON files.
        *   `__init__.py`: Makes `core` a Python package.
    *   `data/`: Default directory for storing `knowledge_graph.json` and `user_progress.json`. Created automatically.
    *   `tests/`: Contains unit tests for the application.
        *   `test_persistence.py`: Tests for data saving/loading.
        *   `test_learning_flow.py`: Tests for content generation and evaluation logic.
        *   `__init__.py`: Makes `tests` a Python package.
*   `README.md`: This file.

## To Do / Future Enhancements

This application is a foundational prototype. Potential future enhancements include:
*   **Real LLM Integration:** Replace all simulated LLM calls with actual API interactions.
*   **Advanced Prerequisite Handling:** Implement a more sophisticated topological sort or adaptive learning path based on prerequisites.
*   **Smarter Content Generation:** Utilize LLMs more effectively for generating varied and high-quality explanations, examples, and questions.
*   **Nuanced Evaluation:** Employ LLMs for evaluating free-form user answers instead of simple keyword matching.
*   **User Authentication:** Implement a proper user system if multiple users are expected.
*   **GUI Interface:** Develop a graphical user interface for a richer user experience.
*   **Expanded Knowledge Representation:** Allow for more complex relationships or content types within the knowledge graph.
*   **Error Handling and Logging:** Implement more robust error handling and application logging.
*   **Configuration File:** Manage settings like `DATA_DIR` or LLM parameters through a configuration file.
```
