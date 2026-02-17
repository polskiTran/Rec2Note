import time
from pathlib import Path

def run_pipeline(file_path: Path):
    """
    Simulates the audio-to-notes pipeline.
    """
    # 1. Simulate Audio Processing
    time.sleep(1.5)

    # 2. Simulate LLM Thinking
    time.sleep(1.5)

    # 3. Return dummy result
    return {
        "title": "Weekly Sync Meeting",
        "summary": "Discussed Q3 goals and marketing budget.",
        "action_items": [
            "John to finalize budget by Friday",
            "Sarah to draft newsletter"
        ]
    }
