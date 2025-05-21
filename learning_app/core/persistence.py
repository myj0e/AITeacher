"""
Handles the saving and loading of application data to/from the file system.

This module provides functions to persist:
- The knowledge graph (list of `KnowledgePoint` objects).
- User progress data (list of `UserProgress` objects).

Data is stored in JSON format in a designated `DATA_DIR`.
"""
import json
import os
from typing import List, Dict, Any # Any is used for generic Dicts in UserProgress
from .data_structures import KnowledgePoint, UserProgress

# --- Constants for Data Storage ---
DATA_DIR = "data" # Directory where data files will be stored, relative to project root.
KNOWLEDGE_GRAPH_FILE = os.path.join(DATA_DIR, "knowledge_graph.json")
USER_PROGRESS_FILE = os.path.join(DATA_DIR, "user_progress.json") # Single file for all users' progress

def ensure_data_dir_exists() -> None:
    """
    Checks if the `DATA_DIR` exists, and if not, creates it.

    This function is called before any file save/load operation to ensure
    the target directory is available. It prints messages regarding its
    actions or any errors encountered.
    """
    if not os.path.exists(DATA_DIR):
        try:
            os.makedirs(DATA_DIR)
            print(f"Data Persistence: Created data directory at '{os.path.abspath(DATA_DIR)}'")
        except OSError as e:
            # This error could occur due to permission issues or other OS-level problems.
            print(f"Data Persistence: Error creating data directory '{os.path.abspath(DATA_DIR)}': {e}")
            # Depending on the application's needs, this might be a critical error.
            # For now, operations will likely fail if the directory can't be created.

def save_knowledge_graph(knowledge_points: List[KnowledgePoint]) -> None:
    """
    Saves the provided list of KnowledgePoint objects to `KNOWLEDGE_GRAPH_FILE`.

    The knowledge graph is serialized to JSON format.

    Args:
        knowledge_points (List[KnowledgePoint]): The list of knowledge points to save.
                                                 Assumes this list forms the complete graph.
    """
    ensure_data_dir_exists()
    try:
        # Convert each KnowledgePoint Pydantic model to its dictionary representation for JSON serialization.
        data_to_save = [kp.model_dump() for kp in knowledge_points]
        with open(KNOWLEDGE_GRAPH_FILE, "w", encoding="utf-8") as f: # Added encoding for robustness
            json.dump(data_to_save, f, indent=4)
        print(f"Data Persistence: Knowledge graph saved to '{KNOWLEDGE_GRAPH_FILE}'")
    except IOError as e: # Specific error for file I/O issues
        print(f"Data Persistence: Error saving knowledge graph to '{KNOWLEDGE_GRAPH_FILE}': {e}")
    except Exception as e: # Catch other potential errors (e.g., Pydantic serialization, unexpected)
        print(f"Data Persistence: An unexpected error occurred while saving knowledge graph: {e}")

def load_knowledge_graph() -> List[KnowledgePoint]:
    """
    Loads the knowledge graph from `KNOWLEDGE_GRAPH_FILE`.

    If the file doesn't exist, is corrupted, or doesn't conform to the expected
    list format, an empty list is returned and an error message is printed.

    Returns:
        List[KnowledgePoint]: A list of `KnowledgePoint` objects loaded from the file.
                              Returns an empty list if loading fails or file is not found.
    """
    ensure_data_dir_exists() 
    if not os.path.exists(KNOWLEDGE_GRAPH_FILE):
        print(f"Data Persistence: Knowledge graph file not found: '{KNOWLEDGE_GRAPH_FILE}'. Returning empty list.")
        return []
    
    try:
        with open(KNOWLEDGE_GRAPH_FILE, "r", encoding="utf-8") as f: # Added encoding
            loaded_data = json.load(f)
            # Basic validation: ensure the loaded data is a list.
            if not isinstance(loaded_data, list):
                print(f"Data Persistence: Knowledge graph data in '{KNOWLEDGE_GRAPH_FILE}' is not a list. File may be malformed. Returning empty list.")
                return []
            # Convert each dictionary back into a KnowledgePoint Pydantic model.
            return [KnowledgePoint(**data) for data in loaded_data]
    except json.JSONDecodeError:
        print(f"Data Persistence: Error decoding JSON from '{KNOWLEDGE_GRAPH_FILE}'. File might be corrupted. Returning empty list.")
        return []
    except IOError as e: # Specific error for file I/O issues
        print(f"Data Persistence: Error loading knowledge graph from '{KNOWLEDGE_GRAPH_FILE}': {e}. Returning empty list.")
        return []
    except Exception as e: # Catch other potential errors (e.g., Pydantic validation, unexpected)
        print(f"Data Persistence: An unexpected error occurred while loading knowledge graph: {e}. Returning empty list.")
        return []

def save_user_progress(user_progress_list: List[UserProgress]) -> None:
    """
    Saves the provided list of UserProgress objects to `USER_PROGRESS_FILE`.

    All user progress records are stored in a single JSON file.

    Args:
        user_progress_list (List[UserProgress]): The list of user progress records to save.
    """
    ensure_data_dir_exists()
    try:
        # Filter out any None values from the list, if they accidentally got in (defensive programming).
        valid_progress_list = [up for up in user_progress_list if up is not None]
        # Convert each UserProgress Pydantic model to its dictionary representation.
        data_to_save = [up.model_dump() for up in valid_progress_list]
        with open(USER_PROGRESS_FILE, "w", encoding="utf-8") as f: # Added encoding
            json.dump(data_to_save, f, indent=4)
        print(f"Data Persistence: User progress saved to '{USER_PROGRESS_FILE}'")
    except IOError as e:
        print(f"Data Persistence: Error saving user progress to '{USER_PROGRESS_FILE}': {e}")
    except Exception as e:
        print(f"Data Persistence: An unexpected error occurred while saving user progress: {e}")


def load_user_progress() -> List[UserProgress]:
    """
    Loads a list of all user progress records from `USER_PROGRESS_FILE`.

    If the file doesn't exist, is corrupted, or doesn't conform to the expected
    list format, an empty list is returned and an error message is printed.

    Returns:
        List[UserProgress]: A list of `UserProgress` objects loaded from the file.
                            Returns an empty list if loading fails or file is not found.
    """
    ensure_data_dir_exists()
    if not os.path.exists(USER_PROGRESS_FILE):
        print(f"Data Persistence: User progress file not found: '{USER_PROGRESS_FILE}'. Returning empty list.")
        return []
    
    try:
        with open(USER_PROGRESS_FILE, "r", encoding="utf-8") as f: # Added encoding
            loaded_data = json.load(f)
            # Basic validation: ensure the loaded data is a list.
            if not isinstance(loaded_data, list):
                print(f"Data Persistence: User progress data in '{USER_PROGRESS_FILE}' is not a list. File may be malformed. Returning empty list.")
                return []
            # Convert each dictionary back into a UserProgress Pydantic model.
            return [UserProgress(**data) for data in loaded_data]
    except json.JSONDecodeError:
        print(f"Data Persistence: Error decoding JSON from '{USER_PROGRESS_FILE}'. File might be corrupted. Returning empty list.")
        return []
    except IOError as e:
        print(f"Data Persistence: Error loading user progress from '{USER_PROGRESS_FILE}': {e}. Returning empty list.")
        return []
    except Exception as e:
        print(f"Data Persistence: An unexpected error occurred while loading user progress: {e}. Returning empty list.")
        return []

# Example of calling ensure_data_dir_exists() at module load time (alternative approach):
# ensure_data_dir_exists()
# However, calling it within each save/load function (as currently implemented)
# is generally more robust, especially if the directory could be deleted
# or become inaccessible during runtime by external factors or other parts of a larger application.
```
