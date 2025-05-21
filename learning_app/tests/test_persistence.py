import sys
import os
import unittest
import json

# Add project root to sys.path to allow direct import of modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.data_structures import KnowledgePoint, UserProgress
from core import persistence # Import the module itself to allow monkeypatching
# from core.persistence import (
#     save_knowledge_graph, load_knowledge_graph,
#     save_user_progress, load_user_progress,
#     ensure_data_dir_exists
# ) # Will use persistence.FUNCTION_NAME for clarity

# --- Global variables for original paths ---
ORIGINAL_KNOWLEDGE_GRAPH_FILE = None
ORIGINAL_USER_PROGRESS_FILE = None
ORIGINAL_DATA_DIR = None


class TestPersistence(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Store original paths before any tests run.
        This is run once for the class.
        """
        global ORIGINAL_KNOWLEDGE_GRAPH_FILE, ORIGINAL_USER_PROGRESS_FILE, ORIGINAL_DATA_DIR
        ORIGINAL_KNOWLEDGE_GRAPH_FILE = persistence.KNOWLEDGE_GRAPH_FILE
        ORIGINAL_USER_PROGRESS_FILE = persistence.USER_PROGRESS_FILE
        ORIGINAL_DATA_DIR = persistence.DATA_DIR

    @classmethod
    def tearDownClass(cls):
        """
        Restore original paths after all tests in the class have run.
        """
        global ORIGINAL_KNOWLEDGE_GRAPH_FILE, ORIGINAL_USER_PROGRESS_FILE, ORIGINAL_DATA_DIR
        persistence.KNOWLEDGE_GRAPH_FILE = ORIGINAL_KNOWLEDGE_GRAPH_FILE
        persistence.USER_PROGRESS_FILE = ORIGINAL_USER_PROGRESS_FILE
        persistence.DATA_DIR = ORIGINAL_DATA_DIR

    def setUp(self):
        """
        Set up test environment before each test method.
        """
        self.test_data_dir = os.path.join(os.path.dirname(__file__), "test_data_persistence") # Unique dir for these tests
        self.test_kp_file = os.path.join(self.test_data_dir, "test_kp.json")
        self.test_up_file = os.path.join(self.test_data_dir, "test_up.json")

        # Monkeypatch the paths in the persistence module for this test
        persistence.DATA_DIR = self.test_data_dir
        persistence.KNOWLEDGE_GRAPH_FILE = self.test_kp_file
        persistence.USER_PROGRESS_FILE = self.test_up_file
        
        # Ensure the test data directory exists
        persistence.ensure_data_dir_exists() # This will now use self.test_data_dir

        # Create dummy data
        self.kp1 = KnowledgePoint(
            id="kp1", name="KP1", description="Desc1",
            explanation_prompt="Explain KP1", example_prompt="Example KP1", test_prompt="Test KP1"
        )
        self.kp2 = KnowledgePoint(
            id="kp2", name="KP2", description="Desc2", prerequisites=["kp1"],
            explanation_prompt="Explain KP2", example_prompt="Example KP2", test_prompt="Test KP2"
        )
        self.sample_knowledge_graph = [self.kp1, self.kp2]

        self.up1 = UserProgress(user_id="user1", knowledge_point_id="kp1", mastery_level=0.5)
        self.up2 = UserProgress(user_id="user1", knowledge_point_id="kp2", mastery_level=0.9)
        self.sample_user_progress = [self.up1, self.up2]

    def tearDown(self):
        """
        Clean up test environment after each test method.
        """
        if os.path.exists(self.test_kp_file):
            os.remove(self.test_kp_file)
        if os.path.exists(self.test_up_file):
            os.remove(self.test_up_file)
        if os.path.exists(self.test_data_dir):
            # Check if directory is empty before removing (safer)
            if not os.listdir(self.test_data_dir):
                 os.rmdir(self.test_data_dir)
            else:
                # If other files were created unexpectedly, print a warning or handle
                print(f"Warning: Test data directory {self.test_data_dir} not empty during teardown.")
                # For safety, remove specific files if they exist, then try rmdir
                if os.path.exists(self.test_kp_file): os.remove(self.test_kp_file)
                if os.path.exists(self.test_up_file): os.remove(self.test_up_file)
                if not os.listdir(self.test_data_dir): os.rmdir(self.test_data_dir)


    def test_ensure_data_dir_exists(self):
        """Test that ensure_data_dir_exists creates the directory."""
        # Remove the directory to test creation
        if os.path.exists(self.test_data_dir):
            # Clean up files first if they exist from a failed previous test or manual intervention
            if os.path.exists(self.test_kp_file): os.remove(self.test_kp_file)
            if os.path.exists(self.test_up_file): os.remove(self.test_up_file)
            os.rmdir(self.test_data_dir) 
        
        self.assertFalse(os.path.exists(self.test_data_dir))
        persistence.ensure_data_dir_exists()
        self.assertTrue(os.path.exists(self.test_data_dir))

    def test_save_and_load_knowledge_graph(self):
        """Test saving and loading of the knowledge graph."""
        persistence.save_knowledge_graph(self.sample_knowledge_graph)
        self.assertTrue(os.path.exists(self.test_kp_file))

        loaded_kps = persistence.load_knowledge_graph()
        self.assertEqual(len(loaded_kps), len(self.sample_knowledge_graph))
        self.assertEqual(loaded_kps[0].id, self.sample_knowledge_graph[0].id)
        self.assertEqual(loaded_kps[1].name, self.sample_knowledge_graph[1].name)

    def test_load_knowledge_graph_file_not_found(self):
        """Test loading knowledge graph when the file does not exist."""
        if os.path.exists(self.test_kp_file): # Ensure it doesn't exist
            os.remove(self.test_kp_file)
        loaded_kps = persistence.load_knowledge_graph()
        self.assertEqual(loaded_kps, [])

    def test_load_knowledge_graph_corrupted_json(self):
        """Test loading knowledge graph from a corrupted JSON file."""
        persistence.ensure_data_dir_exists() # ensure dir is there
        with open(self.test_kp_file, "w") as f:
            f.write("this is not json")
        
        loaded_kps = persistence.load_knowledge_graph()
        self.assertEqual(loaded_kps, []) # Expect graceful handling

        # Test with empty list in JSON (valid JSON, but might be edge case)
        with open(self.test_kp_file, "w") as f:
            json.dump([], f)
        loaded_kps_empty_list = persistence.load_knowledge_graph()
        self.assertEqual(loaded_kps_empty_list, [])
        
        # Test with non-list JSON (e.g. a dictionary at the root)
        with open(self.test_kp_file, "w") as f:
            json.dump({"oops": "not a list"}, f)
        loaded_kps_dict_root = persistence.load_knowledge_graph()
        self.assertEqual(loaded_kps_dict_root, [])


    def test_save_and_load_user_progress(self):
        """Test saving and loading of user progress."""
        persistence.save_user_progress(self.sample_user_progress)
        self.assertTrue(os.path.exists(self.test_up_file))

        loaded_ups = persistence.load_user_progress()
        self.assertEqual(len(loaded_ups), len(self.sample_user_progress))
        self.assertEqual(loaded_ups[0].user_id, self.sample_user_progress[0].user_id)
        self.assertEqual(loaded_ups[1].knowledge_point_id, self.sample_user_progress[1].knowledge_point_id)
        self.assertAlmostEqual(loaded_ups[1].mastery_level, self.sample_user_progress[1].mastery_level)

    def test_load_user_progress_file_not_found(self):
        """Test loading user progress when the file does not exist."""
        if os.path.exists(self.test_up_file): # Ensure it doesn't exist
            os.remove(self.test_up_file)
        loaded_ups = persistence.load_user_progress()
        self.assertEqual(loaded_ups, [])

    def test_load_user_progress_corrupted_json(self):
        """Test loading user progress from a corrupted JSON file."""
        persistence.ensure_data_dir_exists() # ensure dir is there
        with open(self.test_up_file, "w") as f:
            f.write("this is not json either")
        
        loaded_ups = persistence.load_user_progress()
        self.assertEqual(loaded_ups, [])

        # Test with empty list in JSON
        with open(self.test_up_file, "w") as f:
            json.dump([], f)
        loaded_ups_empty_list = persistence.load_user_progress()
        self.assertEqual(loaded_ups_empty_list, [])

        # Test with non-list JSON
        with open(self.test_up_file, "w") as f:
            json.dump({"error": "not a list of progresses"}, f)
        loaded_ups_dict_root = persistence.load_user_progress()
        self.assertEqual(loaded_ups_dict_root, [])

if __name__ == '__main__':
    unittest.main()
