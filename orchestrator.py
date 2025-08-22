# orchestrator.py
# This file contains the core logic for the multi-agent system, including
# the Orchestrator that manages the workflow and the HistoryStore for data persistence.

import sqlite3
import time
from dataclasses import dataclass, asdict
from typing import Dict, Any, List
from colorama import Fore, Style, init

from agents import FakeLLM, HuggingFaceAgent, _TRANSFORMERS_OK
from tools import find_available_calendar_slot, book_calendar_event

init(autoreset=True)

@dataclass
class Contribution:
    role: str
    answer: str
    confidence: float
    rationale: str
    iteration: int

class HistoryStore:
    def __init__(self, path: str = "collab_history.db") -> None:
        self.path = path
        self._init()

    def _init(self) -> None:
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, role TEXT NOT NULL,
                answer TEXT NOT NULL, confidence REAL NOT NULL, rationale TEXT NOT NULL, iteration INTEGER NOT NULL
            )
            """
        )
        con.commit()
        con.close()

    def log(self, c: Contribution) -> None:
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(
            "INSERT INTO contributions (ts, role, answer, confidence, rationale, iteration) VALUES (?,?,?,?,?,?)",
            (time.time(), c.role, c.answer, c.confidence, c.rationale, c.iteration),
        )
        con.commit()
        con.close()

    def latest(self, limit: int = 10) -> List[Contribution]:
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(
            "SELECT role, answer, confidence, rationale, iteration FROM contributions ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = cur.fetchall()
        con.close()
        return [Contribution(role, answer, confidence, rationale, iteration) for role, answer, confidence, rationale, iteration in rows]

class Orchestrator:
    """Manages the entire multi-agent collaboration workflow."""
    def __init__(self, store: HistoryStore, rounds: int = 2, use_hf: bool = False):
        self.store = store
        self.rounds = rounds
        self.use_hf = use_hf
        self.board: Dict[str, Dict[str, Any]] = {}
        self.agents: Dict[str, Any] = {}
        self.moderator: Any = None

    def _print_header(self, t: str) -> None:
        print("\n" + Fore.CYAN + "╔" + "═" * (len(t) + 2) + "╗")
        print(Fore.CYAN + f"║ {t} ║")
        print(Fore.CYAN + "╚" + "═" * (len(t) + 2) + "╝" + Style.RESET_ALL)

    def _print_agent_output(self, role: str, output: str, iteration: int = 1):
        role_colors = {
            "ResearchBot": Fore.BLUE, "CreativeBot": Fore.MAGENTA,
            "AnalysisBot": Fore.GREEN, "Moderator": Fore.YELLOW,
            "TranscriptSummarizer": Fore.GREEN, "ActionItemExtractor": Fore.BLUE
        }
        color = role_colors.get(role, Fore.WHITE)
        print(color + f"\n▶ [{role} - Round {iteration}]" + Style.RESET_ALL)
        for line in output.split('\n'):
            print(f"  {line}")

    def _board_text(self) -> str:
        if not self.board:
            return "(empty)"
        parts = []
        for agent_id in sorted(self.board.keys()):
            data = self.board[agent_id]
            parts.append(f"--- Contribution from {agent_id} ---\n{data['answer']}")
        return "\n\n".join(parts)

    # FIX: The missing method is now restored.
    def run_research_collaboration(self, task: str):
        self._print_header(f"SCENARIO 1: Research Collaboration on '{task}'")
        
        if self.use_hf:
            self.agents = {
                "ResearchBot": HuggingFaceAgent("ResearchBot", "microsoft/phi-2"),
                "CreativeBot": HuggingFaceAgent("CreativeBot", "microsoft/phi-2"),
                "AnalysisBot": HuggingFaceAgent("AnalysisBot", "facebook/bart-large-cnn"),
            }
            self.moderator = HuggingFaceAgent("Moderator", "microsoft/phi-2")
        else:
            self.agents = { "ResearchBot": FakeLLM("ResearchBot"), "CreativeBot": FakeLLM("CreativeBot"), "AnalysisBot": FakeLLM("AnalysisBot") }
            self.moderator = FakeLLM("Moderator")
        
        final_report = "No conclusion reached after maximum rounds."
        for r in range(1, self.rounds + 1):
            print(Fore.CYAN + f"\n--- Starting Round {r} ---")
            for role, agent in self.agents.items():
                output = agent.generate(task, self._board_text())
                contrib = Contribution(role, output, 0.8, "generated", r)
                self.store.log(contrib)
                self.board[f"{role}-r{r}"] = asdict(contrib)
                self._print_agent_output(role, output, r)

            mod_output = self.moderator.generate(task, self._board_text())
            contrib = Contribution("Moderator", mod_output, 0.9, "review", r)
            self.store.log(contrib)
            self.board[f"Moderator-r{r}"] = asdict(contrib)
            self._print_agent_output("Moderator", mod_output, r)
            
            if mod_output.strip().upper().startswith("CONCLUSION:"):
                print(Fore.GREEN + "\n--- Moderator concluded the task is complete. ---")
                final_report = mod_output.replace("CONCLUSION:", "").strip()
                self._print_header("FINAL REPORT (SCENARIO 1)")
                print(Fore.GREEN + final_report)
                return {"board": self.board, "final": {"summary": final_report}}
            else:
                print(Fore.YELLOW + f"\n--- Moderator requested another round of revisions. ---")
        
        self._print_header("FINAL REPORT (SCENARIO 1)")
        print(Fore.GREEN + final_report)
        return {"board": self.board, "final": {"summary": final_report}}

    def run_schedule_optimization(self, transcript: str):
        self._print_header(f"SCENARIO 2: Schedule Optimization")

        self.agents = {
            "TranscriptSummarizer": HuggingFaceAgent("TranscriptSummarizer", "facebook/bart-large-cnn"),
            "ActionItemExtractor": HuggingFaceAgent("ActionItemExtractor", "microsoft/phi-2"),
        }
        self.moderator = HuggingFaceAgent("Moderator", "microsoft/phi-2")
        
        task = f"Analyze the following transcript, summarize it, and extract the key action item. Transcript:\n{transcript}"
        
        summary = self.agents["TranscriptSummarizer"].generate(task, transcript)
        contrib = Contribution("TranscriptSummarizer", summary, 0.8, "generated", 1)
        self.store.log(contrib)
        self.board["TranscriptSummarizer-r1"] = asdict(contrib)
        self._print_agent_output("TranscriptSummarizer", summary)
        
        action_item_task = "Based on the transcript and summary, what is the single most important follow-up action item that requires scheduling? Respond with only the action itself."
        action_items = self.agents["ActionItemExtractor"].generate(action_item_task, self._board_text())
        contrib = Contribution("ActionItemExtractor", action_items, 0.8, "generated", 1)
        self.store.log(contrib)
        self.board["ActionItemExtractor-r1"] = asdict(contrib)
        self._print_agent_output("ActionItemExtractor", action_items)
        
        final_report_text = "CONCLUSION: No specific scheduling action item was identified."
        meeting_title = ""
        
        action_lower = action_items.lower()
        if "schedule" in action_lower or "finalize" in action_lower or "review" in action_lower:
            if "budget" in action_lower:
                meeting_title = "Finalize Q4 Budget"
            elif "report" in action_lower:
                meeting_title = "Review Detailed Report"
            else:
                meeting_title = "General Follow-up Meeting"

            print(Fore.CYAN + "\n--- Executing Scheduling Task based on AI output ---")
            follow_up_time = find_available_calendar_slot(duration_minutes=45)
            success = book_calendar_event(
                time_slot=follow_up_time,
                title=meeting_title,
                description=f"Follow-up based on meeting summary: {summary}"
            )
            if success:
                final_report_text = f"SUCCESS: Follow-up meeting '{meeting_title}' scheduled for {follow_up_time}."
            else:
                final_report_text = "FAILURE: Could not schedule the meeting."

        contrib = Contribution("Moderator", final_report_text, 0.9, "conclusion", 1)
        self.store.log(contrib)
        self._print_header("FINAL REPORT (SCENARIO 2)")
        print(Fore.GREEN + final_report_text)