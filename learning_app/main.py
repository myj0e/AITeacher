"""
Main entry point for the Personalized Learning App.

This script orchestrates the user's learning experience. It handles:
- Loading and saving the knowledge graph and user progress.
- Interacting with the user to determine learning goals.
- Generating or loading a learning path (knowledge graph).
- Iterating through knowledge points, providing explanations, examples, and tests.
- Tracking user mastery and saving progress.

The application uses simulated LLM responses for content generation and
knowledge graph creation. Actual LLM integration is a future enhancement.
"""
import os
import datetime # For timestamping learning history
from typing import List, Dict, Any

# --- Core Application Imports ---
from learning_app.core.llm_interaction import generate_knowledge_graph, get_relationships
from learning_app.core.learning_flow import get_concept_explanation, get_example, get_test_questions, evaluate_answer
from learning_app.core.data_structures import KnowledgePoint, UserProgress
from learning_app.core.persistence import (
    save_knowledge_graph, load_knowledge_graph,
    save_user_progress, load_user_progress,
    KNOWLEDGE_GRAPH_FILE # Used to check for existing graph before prompting for a new goal
)

# --- Global Configuration ---
USER_ID = "default_user" # Placeholder for user identification. In a multi-user system, this would be dynamic.

# --- Helper Functions for CLI Interaction ---
def get_yes_no_input(prompt: str) -> bool:
    """
    Gets a yes/no answer from the user, case-insensitive. Accepts 'y'/'n' and 'yes'/'no'.

    Args:
        prompt (str): The question to ask the user.

    Returns:
        bool: True if the user answers yes, False if the user answers no.
    """
    while True:
        choice = input(f"{prompt} (y/n or yes/no): ").strip().lower()
        if choice in ['y', 'yes']:
            return True
        elif choice in ['n', 'no']:
            return False
        else:
            print("Invalid input. Please enter 'y', 'yes', 'n', or 'no'.")

def print_section_header(title: str) -> None:
    """
    Prints a consistently formatted section header to the console.

    Args:
        title (str): The title for the section.
    """
    # Calculate dynamic padding for centering based on a nominal width of 50
    padding = (50 - len(title) - 5) # 5 for '=== ' and ' ==='
    padding = max(0, padding) # Ensure padding is not negative
    print(f"\n{'=' * 3} {title.upper()} {'=' * padding}")

def print_knowledge_graph(knowledge_points: List[KnowledgePoint]) -> None:
    """
    Prints a user-friendly representation of the knowledge graph, including prerequisites.

    Args:
        knowledge_points (List[KnowledgePoint]): The list of knowledge points in the graph.
    """
    if not knowledge_points:
        print_section_header("Learning Path")
        print("No knowledge graph to display.")
        return
    
    print_section_header("Your Learning Path")
    kp_map = {kp.id: kp for kp in knowledge_points} # For efficient prerequisite name lookup

    for i, kp in enumerate(knowledge_points):
        prereq_names = [kp_map[pr_id].name for pr_id in kp.prerequisites if pr_id in kp_map]
        prereq_str = f"(Prerequisites: {', '.join(prereq_names)})" if prereq_names else "(No prerequisites)"
        # Displaying index, name, a snippet of description, and prerequisites
        print(f"  {i+1}. {kp.name} - {kp.description[:60]}... {prereq_str}")


def print_test_feedback(is_correct: bool, question: Dict[str, Any]) -> None:
    """
    Prints feedback to the user after they answer a test question.

    Args:
        is_correct (bool): Whether the user's answer was correct.
        question (Dict[str, Any]): The question object, used to provide more detailed
                                   feedback (e.g., the correct answer for MCQs).
    """
    if is_correct:
        print("✅ Correct!")
    else:
        feedback = "❌ Incorrect."
        # Provide more specific feedback if available in the question data
        if question['type'] == 'multiple_choice' and 'correct_answer' in question:
            feedback += f" The correct answer was: '{question['correct_answer']}'"
        elif question['type'] == 'short_answer' and 'correct_answer_description' in question:
            # For short answers, a description of the expected answer is often more helpful than just keywords
            feedback += f" Expected focus: {question['correct_answer_description']}"
        print(feedback)

# --- Main Application Logic ---
def main_learning_loop() -> None:
    """
    Orchestrates the main interactive learning loop for the user.

    This function guides the user through:
    1. Loading existing data (knowledge graph and user progress).
    2. Deciding whether to continue an existing path or start a new one.
    3. Generating a new knowledge graph if requested.
    4. Iterating through knowledge points, offering explanations, examples, and tests.
    5. Tracking mastery and saving progress after each interaction.
    """
    print_section_header("Application Start")
    print("Loading existing learning data...")
    loaded_knowledge_graph = load_knowledge_graph()
    all_user_progress_list = load_user_progress() # Contains progress for all users (if any)

    # Segregate progress for the current user from others
    current_user_progress_map: Dict[str, UserProgress] = {} # Keyed by knowledge_point_id
    other_users_progress_list: List[UserProgress] = [] # To preserve other users' data

    for up_entry in all_user_progress_list:
        if up_entry.user_id == USER_ID:
            current_user_progress_map[up_entry.knowledge_point_id] = up_entry
        else:
            other_users_progress_list.append(up_entry)

    knowledge_points: List[KnowledgePoint] = []
    user_wants_new_graph = False # Flag to indicate if user opted for a new graph

    # --- Knowledge Graph Selection/Generation ---
    if loaded_knowledge_graph:
        print_section_header("Existing Learning Path Found")
        print_knowledge_graph(loaded_knowledge_graph)
        if get_yes_no_input("Do you want to continue with this path?"):
            knowledge_points = loaded_knowledge_graph
        else:
            user_wants_new_graph = True # User wants to create a new graph
    
    # If no graph is loaded yet, or user wants a new one
    if not knowledge_points or user_wants_new_graph:
        prompt_for_new_goal = True # Assume we need to ask for a new goal
        if os.path.exists(KNOWLEDGE_GRAPH_FILE) and user_wants_new_graph:
             # If a graph file exists but user wants a new one, confirm they want to define a new goal
             prompt_for_new_goal = get_yes_no_input(
                 "Do you want to define a new learning goal? "
                 "(Choosing 'no' will try to use the most recent graph if you change your mind about starting over)"
             )
             if not prompt_for_new_goal and loaded_knowledge_graph:
                 # User changed mind, wants to use existing graph after all
                 knowledge_points = loaded_knowledge_graph
                 user_wants_new_graph = False # Revert this decision
             elif not prompt_for_new_goal and not loaded_knowledge_graph:
                  print("No existing learning path to fall back on. Exiting.")
                  return

        # Proceed to get new goal and generate graph if needed
        if prompt_for_new_goal and (not os.path.exists(KNOWLEDGE_GRAPH_FILE) or user_wants_new_graph):
            learning_goal = input("What do you want to learn today? (e.g., 'Python basics', 'data analysis with Pandas'): ")
            print("\nGenerating your personalized learning path... this might take a moment.")
            new_kps = generate_knowledge_graph(learning_goal)
            
            if new_kps: # Successfully generated some KPs
                knowledge_points = get_relationships(new_kps) # Establish connections
                save_knowledge_graph(knowledge_points) # Save the new graph
                print("New learning path generated and saved.")
            else: # Failed to generate KPs
                print("Sorry, I couldn't generate a learning path for that goal right now.")
                if loaded_knowledge_graph: # Offer fallback to previously loaded graph if available
                    if get_yes_no_input("Do you want to revert to your previously loaded learning path?"):
                        knowledge_points = loaded_knowledge_graph
                        user_wants_new_graph = False # Revert this flag
                    else:
                        print("No learning path to proceed with. Exiting.")
                        return
                else: # No new KPs and no old graph to fall back on
                    print("No learning path available. Exiting.")
                    return
        elif loaded_knowledge_graph and not user_wants_new_graph: 
            # This branch is reached if user chose 'c' (continue) with loaded_knowledge_graph
            knowledge_points = loaded_knowledge_graph
        elif not loaded_knowledge_graph and not prompt_for_new_goal:
             # This case: user opted for new graph, then said 'no' to defining new goal, and no prior graph loaded.
             print("No learning path to proceed with. Exiting.")
             return

    if not knowledge_points: # Final check if a graph is available
        print("No learning path available to start. Exiting.")
        return

    # Display the active learning path if it wasn't just generated and printed
    if not user_wants_new_graph : # This condition might need refinement to avoid re-printing if not desired
        print_knowledge_graph(knowledge_points)

    # --- Initialize Mastered KPs based on Loaded Progress ---
    mastered_kp_ids = set()
    for kp_id, progress_entry in current_user_progress_map.items():
        # Find the corresponding KP in the current graph (if it exists)
        kp_reference = next((kp for kp in knowledge_points if kp.id == kp_id), None)
        if kp_reference and progress_entry.mastery_level >= kp_reference.mastery_threshold:
            mastered_kp_ids.add(kp_id)
    
    if mastered_kp_ids:
        print_section_header("Previously Mastered Topics")
        mastered_names = [kp.name for kp in knowledge_points if kp.id in mastered_kp_ids]
        print(f"Based on your history, you have already mastered: {', '.join(mastered_names) if mastered_names else 'None'}")
    else:
        print("\nStarting fresh! No previously mastered topics found for this learning path.")

    # --- Main Learning Iteration Loop ---
    for current_kp_index, current_kp in enumerate(knowledge_points):
        print_section_header(f"Topic: {current_kp.name}")
        
        # Basic prerequisite check
        if not all(prereq_id in mastered_kp_ids for prereq_id in current_kp.prerequisites):
            required_prereq_names = [kp.name for kp_id_req in current_kp.prerequisites for kp in knowledge_points if kp.id == kp_id_req]
            current_mastered_names = [kp.name for kp_id_mast in mastered_kp_ids for kp in knowledge_points if kp.id == kp_id_mast]
            print(f"Skipping '{current_kp.name}' for now. Prerequisites not yet met/mastered in this session.")
            print(f"  Required: {', '.join(required_prereq_names) or 'None'}")
            print(f"  Mastered so far: {', '.join(current_mastered_names) or 'None'}")
            continue # Skip to the next knowledge point

        print(f"Description: {current_kp.description}")

        # Check for existing progress on this specific KP
        if current_kp.id in current_user_progress_map:
            existing_progress = current_user_progress_map[current_kp.id]
            print(f"\nWelcome back! You previously achieved {existing_progress.mastery_level*100:.0f}% mastery on this topic.")
            if existing_progress.mastery_level >= current_kp.mastery_threshold:
                print("You have already mastered this topic according to your records.")
                if not get_yes_no_input("Do you want to review and re-test this topic anyway?"):
                    mastered_kp_ids.add(current_kp.id) # Ensure it's in the set for this session
                    continue # Skip to next topic
        
        # Display Explanation
        print_section_header(f"Explanation: {current_kp.name}")
        explanation = get_concept_explanation(current_kp)
        print(explanation)
        
        # Offer Example
        if get_yes_no_input("Would you like to see an example for this topic?"):
            print_section_header(f"Example: {current_kp.name}")
            example = get_example(current_kp)
            print(example)

        # Administer Test
        print_section_header(f"Test: {current_kp.name}")
        questions = get_test_questions(current_kp)
        correct_answers_count = 0
        score = 0.0 # Default score if no questions

        if not questions:
            print("No test questions available for this topic.")
        else:
            for i, question_data in enumerate(questions):
                print(f"\nQuestion {i+1}/{len(questions)}: {question_data['question_text']}")
                user_answer_submission = "" # Store the processed answer for evaluation
                if question_data['type'] == 'multiple_choice':
                    options = question_data.get('options', [])
                    for opt_idx, option_text in enumerate(options):
                        print(f"  {chr(97+opt_idx)}) {option_text}") # e.g., a) Option 1
                    
                    while True: # Loop until valid option letter is entered
                        ans_choice_letter = input("Your choice (e.g., 'a', 'b'): ").strip().lower()
                        if len(ans_choice_letter) == 1 and 'a' <= ans_choice_letter < chr(97 + len(options)):
                            user_answer_submission = options[ord(ans_choice_letter) - ord('a')] # Get the actual option text
                            break
                        else:
                            print(f"Invalid choice. Please enter a letter between 'a' and '{chr(97 + len(options) -1)}'.")
                else: # For 'short_answer' or other types
                    user_answer_submission = input("Your answer: ").strip()
                
                is_correct = evaluate_answer(question_data, user_answer_submission)
                print_test_feedback(is_correct, question_data)
                if is_correct:
                    correct_answers_count += 1
            
            score = correct_answers_count / len(questions) if questions else 0.0 # Calculate score
        
        print(f"\nYou scored {score*100:.0f}% on the test for {current_kp.name}.")

        # Update UserProgress for this KP
        user_progress_entry = current_user_progress_map.get(current_kp.id)
        if not user_progress_entry: # First time encountering this KP for this user
            user_progress_entry = UserProgress(
                user_id=USER_ID, 
                knowledge_point_id=current_kp.id,
                mastery_level=score,
                learning_history=[] # Initialize history
            )
        else: # Update existing progress
            user_progress_entry.mastery_level = max(user_progress_entry.mastery_level, score) # Keep highest score
        
        # Add current attempt to learning history
        user_progress_entry.learning_history.append({
            "action": "test_attempt", 
            "score": score, 
            "timestamp": datetime.datetime.now().isoformat() # Use standard ISO format
        })
        current_user_progress_map[current_kp.id] = user_progress_entry # Update map
        
        # Save all progress (current user's updated, plus others')
        updated_all_user_progress_list = list(current_user_progress_map.values()) + other_users_progress_list
        save_user_progress(updated_all_user_progress_list)
        print("Your progress has been saved.")

        # Update mastered set for current session and provide feedback
        if user_progress_entry.mastery_level >= current_kp.mastery_threshold:
            print("🎉 Congratulations! You've demonstrated good understanding of this topic. 🎉")
            mastered_kp_ids.add(current_kp.id)
        else:
            print("Keep practicing! You'll get it. Consider reviewing the explanation and examples again.")
        
        # Ask to continue to next topic or exit
        if current_kp_index < len(knowledge_points) - 1: # If not the last topic
            if not get_yes_no_input("\nContinue to the next topic?"):
                print("Exiting learning session. Your progress is saved.")
                break # Exit the learning loop
        else: # Last topic completed
            print_section_header("Learning Path Complete")
            print("You have reached the end of your current learning path! Well done!")


# --- Application Entry Point ---
if __name__ == "__main__":
    # Main execution block when script is run directly
    print("=" * 60) # Wider border for main welcome/goodbye
    print("🎉 WELCOME TO THE PERSONALIZED LEARNING APP! 🎉")
    print("=" * 60)
    try:
        main_learning_loop()
    except KeyboardInterrupt: # Handle Ctrl+C gracefully
        print("\n\nExiting application via keyboard interrupt. Your progress should be saved if applicable.")
    except Exception as e: # Catch any other unexpected errors
        print(f"\nAn unexpected error occurred: {e}")
        print("If this issue persists, please consider reporting it or checking the application logs.")
        # For debugging purposes, one might uncomment the following lines:
        # import traceback
        # traceback.print_exc()
    finally:
        print("\n" + "=" * 60)
        print("👋 GOODBYE! HOPE YOU LEARNED SOMETHING NEW! 👋")
        print("=" * 60)
```
