# agents.py
# This file contains the agent backends, defining the "brains" of the operation.
# It includes a mock agent for testing and a real agent that connects to Hugging Face models.

_TRANSFORMERS_OK = False
try:
    from transformers import pipeline
    _TRANSFORMERS_OK = True
except ImportError:
    pipeline = None

class FakeLLM:
    """A deterministic, rule-based mock agent for fast and reliable unit testing."""
    def __init__(self, role: str):
        self.role = role

    def generate(self, task: str, board: str) -> str:
        task_lower = task.lower()
        context = board if board and board != "(empty)" else task
        
        if self.role == "ResearchBot":
            if "capital of france" in task_lower:
                return "Paris is the capital of France, known for the Eiffel Tower."
            if "capital of india" in task_lower:
                return "New Delhi"
            return f"(fact guess about: {task[:40]}...)"
        if self.role == "CreativeBot":
            return f"A whimsical story about: {context}"
        if self.role == "AnalysisBot":
            return f"Key points from the board: {context[:60]}"
        if self.role == "Moderator":
            if "Paris" in context or "New Delhi" in context:
                return "CONCLUSION: The report is complete."
            else:
                return "NEXT_STEP: The research is incomplete."
        return f"Unhandled role {self.role}"

class HuggingFaceAgent:
    """An agent that uses real AI models from the Hugging Face Hub."""
    def __init__(self, role: str, model_name: str):
        self.role = role
        task = "summarization" if "Summarizer" in role or "Analysis" in role else "text-generation"
        self.pipe = pipeline(task, model=model_name, trust_remote_code=True)

    def generate(self, task: str, board: str) -> str:
        if "Summarizer" in self.role or "Analysis" in self.role:
            try:
                text_to_summarize = board if len(board) > 50 else task
                response = self.pipe(text_to_summarize, max_length=100, min_length=20, truncation=True)
                return response[0]['summary_text']
            except Exception as e:
                return f"Error during summarization: {e}"
        
        prompt = ""
        if self.role == "ResearchBot":
            prompt = f"Instruct: You are a research assistant. Provide a detailed, factual summary of the following topic.\nInput: {task}\nOutput:"
        elif self.role == "CreativeBot":
            prompt = f"Instruct: You are a creative writer. Write an engaging narrative based on the provided text.\nInput: {board}\nOutput:"
        else: 
            prompt = f"Instruct: Analyze the following text and perform this task: {task}\nInput: {board}\nOutput:"
        
        try:
            response = self.pipe(prompt, max_new_tokens=200, do_sample=True, temperature=0.7)
            full_response = response[0]['generated_text']
            output_start = full_response.find("Output:")
            if output_start != -1:
                return full_response[output_start + len("Output:"):].strip()
            return full_response
        except Exception as e:
            return f"Error generating text: {e}"