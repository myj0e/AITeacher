import sys
import os
import unittest

# Add project root to sys.path to allow direct import of modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.data_structures import KnowledgePoint
from core.learning_flow import (
    get_concept_explanation, 
    get_example, 
    get_test_questions, 
    evaluate_answer
)

class TestLearningFlow(unittest.TestCase):

    def setUp(self):
        """Set up a sample KnowledgePoint for testing."""
        self.sample_kp = KnowledgePoint(
            id="kp_test_flow",
            name="Test Topic",
            description="A topic for testing learning flow functions.",
            explanation_prompt="Explain the Test Topic.",
            example_prompt="Show an example of the Test Topic.",
            test_prompt="Test understanding of the Test Topic's core concepts.",
            mastery_threshold=0.75,
            prerequisites=["kp_test_prereq"],
            postrequisites=["kp_test_postreq"]
        )

    def test_get_concept_explanation(self):
        """Test that get_concept_explanation returns a string containing the KP's name."""
        explanation = get_concept_explanation(self.sample_kp)
        self.assertIsInstance(explanation, str)
        self.assertIn(self.sample_kp.name, explanation)
        # Check if the placeholder content is present (based on current implementation)
        self.assertIn("placeholder explanation", explanation.lower())

    def test_get_example(self):
        """Test that get_example returns a string containing the KP's name."""
        example = get_example(self.sample_kp)
        self.assertIsInstance(example, str)
        self.assertIn(self.sample_kp.name, example)
        # Check if the placeholder content is present
        self.assertIn("placeholder example", example.lower())

    def test_get_test_questions(self):
        """Test that get_test_questions returns a list of question dictionaries with expected keys."""
        questions = get_test_questions(self.sample_kp)
        self.assertIsInstance(questions, list)
        self.assertTrue(len(questions) > 0, "Should return at least one question.")

        for question in questions:
            self.assertIsInstance(question, dict)
            self.assertIn("question_id", question)
            self.assertIn("question_text", question)
            self.assertIn("type", question)
            # Depending on type, other keys should be present
            if question["type"] == "multiple_choice":
                self.assertIn("options", question)
                self.assertIn("correct_answer", question)
            elif question["type"] == "short_answer":
                self.assertIn("correct_answer_keywords", question) # As per current implementation
            
            # Check if the KP's name is somehow reflected in the question (as per placeholder logic)
            self.assertTrue(
                self.sample_kp.name in question["question_text"] or 
                self.sample_kp.id in question["question_id"]
            )

    def test_evaluate_answer_multiple_choice(self):
        """Test evaluation of multiple-choice answers."""
        sample_mcq = {
            "question_id": "test_mcq1",
            "question_text": "What is 1+1?",
            "type": "multiple_choice",
            "options": ["1", "2", "3", "4"],
            "correct_answer": "2",
            "llm_eval_prompt": "N/A for this test"
        }
        self.assertTrue(evaluate_answer(sample_mcq, "2"))
        self.assertTrue(evaluate_answer(sample_mcq, " 2 ")) # Test with whitespace
        self.assertFalse(evaluate_answer(sample_mcq, "1"))
        self.assertFalse(evaluate_answer(sample_mcq, "Two")) # Current logic is exact string match
        self.assertFalse(evaluate_answer(sample_mcq, ""))
        self.assertFalse(evaluate_answer(sample_mcq, None))

    def test_evaluate_answer_short_answer(self):
        """Test evaluation of short-answer questions based on keywords."""
        sample_saq = {
            "question_id": "test_saq1",
            "question_text": "What are Python's main data types?",
            "type": "short_answer",
            "correct_answer_keywords": ["integer", "string", "list", "dictionary"],
            "llm_eval_prompt": "N/A for this test",
            "correct_answer_description": "Core Python data types."
        }
        
        correct_ans = "Python uses integer, string, list, and dictionary types."
        self.assertTrue(evaluate_answer(sample_saq, correct_ans))
        
        correct_ans_case = "python uses INTEGER, STRING, LIST, and DICTIONARY types."
        self.assertTrue(evaluate_answer(sample_saq, correct_ans_case)) # Test case-insensitivity (due to .lower())

        partial_ans = "Python has integer and string."
        self.assertFalse(evaluate_answer(sample_saq, partial_ans)) # Missing list, dictionary

        irrelevant_ans = "Java is a programming language."
        self.assertFalse(evaluate_answer(sample_saq, irrelevant_ans))

        empty_ans = ""
        self.assertFalse(evaluate_answer(sample_saq, empty_ans))
        
        none_ans = None
        self.assertFalse(evaluate_answer(sample_saq, none_ans))

    def test_evaluate_answer_short_answer_no_keywords(self):
        """Test short-answer evaluation when no keywords are defined (placeholder behavior)."""
        sample_saq_no_keywords = {
            "question_id": "test_saq_no_kw",
            "question_text": "Explain quantum physics.",
            "type": "short_answer",
            "correct_answer_keywords": [], # No keywords
            "llm_eval_prompt": "N/A",
            "correct_answer_description": "Complex topic."
        }
        # Current placeholder logic for no keywords returns False
        self.assertFalse(evaluate_answer(sample_saq_no_keywords, "Anything will do here")) 
        self.assertFalse(evaluate_answer(sample_saq_no_keywords, ""))

    def test_evaluate_answer_unknown_type(self):
        """Test evaluation of an unknown question type."""
        sample_unknown_q = {
            "question_id": "test_unknown_q1",
            "question_text": "A trick question.",
            "type": "essay", # Not currently handled by simple evaluation
            "correct_answer": "N/A"
        }
        self.assertFalse(evaluate_answer(sample_unknown_q, "Some long answer."))

if __name__ == '__main__':
    unittest.main()
