from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = PROJECT_ROOT / "agent.log"
CALL_COUNT = 0


def clear_log() -> None:
    global CALL_COUNT
    CALL_COUNT = 0
    with LOG_PATH.open("w", encoding="utf-8"):
        pass


def log_request(user_prompt: str) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write("Request:\n")
        file.write(f"{user_prompt}\n")
        file.write("\n===\n\n")


def log_response(response: str, label: str = "Response") -> None:
    global CALL_COUNT
    CALL_COUNT += 1

    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(f"{label} {CALL_COUNT}\n")
        file.write(f"{response}\n\n")


def log_validation_error(reason: str, response: str) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write("Validation Error\n")
        file.write(f"Reason: {reason}\n")
        file.write("Response:\n")
        file.write(f"{response}\n\n")


def log_repair_attempt(repair_kind: str, reason: str) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write("Repair Attempt\n")
        file.write(f"Kind: {repair_kind}\n")
        file.write(f"Reason: {reason}\n\n")
