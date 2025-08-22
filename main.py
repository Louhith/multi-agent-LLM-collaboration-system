# main.py
# This is the main entry point for the application. Its primary role is to
# orchestrate the high-level workflow: running tests and then executing the main demos.

import os
from orchestrator import Orchestrator, HistoryStore
from agents import _TRANSFORMERS_OK
from tools import get_meeting_transcript, find_available_calendar_slot, book_calendar_event
from graphviz import Digraph

def run_research_demo(topic: str, use_hf: bool = False, rounds: int = 2) -> None:
    """Runs a demonstration of the research collaboration agent (Scenario 1)."""
    db_path = "research_history.db"
    # if os.path.exists(db_path):
    #     os.remove(db_path)
    
    store = HistoryStore(path=db_path)
    orch = Orchestrator(store=store, rounds=rounds, use_hf=use_hf)
    orch.run_research_collaboration(topic)

def run_schedule_demo(meeting_id: str) -> None:
    """Runs a demonstration of the schedule optimization agent (Scenario 2)."""
    db_path = "schedule_history.db"
    # if os.path.exists(db_path):
    #     os.remove(db_path)
        
    store = HistoryStore(path=db_path)
    orch = Orchestrator(store=store, use_hf=True, rounds=1)
    
    transcript = get_meeting_transcript(meeting_id)
    orch.run_schedule_optimization(transcript)

def test_history_created() -> None:
    """Unit test to verify that the HistoryStore correctly creates a database."""
    print("\n--- TEST: test_history_created ---")
    path = "collab_history_test.db"
    if os.path.exists(path):
        os.remove(path)
    orch = Orchestrator(store=HistoryStore(path), rounds=1)
    _ = orch.run_research_collaboration("What is the capital of France?")
    assert os.path.exists(path), "Expected test db to be created"
    os.remove(path)
    print("PASS")

def test_research_path() -> None:
    """Unit test to verify the FakeLLM's deterministic logic."""
    print("\n--- TEST: test_research_path (FakeLLM) ---")
    path = "collab_history_test.db"
    if os.path.exists(path):
        os.remove(path)
    orch = Orchestrator(store=HistoryStore(path), rounds=1)
    _ = orch.run_research_collaboration("What is the capital of India?")
    
    # FIX: Restored the assertion to make the test meaningful.
    rows = orch.store.latest(10)
    research_answers = [c.answer for c in rows if c.role == "ResearchBot"]
    assert any("New Delhi" in a for a in research_answers), "Expected ResearchBot to answer 'New Delhi'"
    
    os.remove(path)
    print("PASS")


if __name__ == "__main__":
    print("--- Running Automated Tests ---")
    test_history_created()
    test_research_path()
    print("\n--- All tests passed successfully ---")

    if _TRANSFORMERS_OK:
        # --- Run Scenario 1: Research Collaboration ---
        run_research_demo("RCB won their first IPL title", use_hf=True, rounds=2)

        # --- Run Scenario 2: Schedule Optimization ---
        run_schedule_demo(meeting_id="meeting_q4_planning")