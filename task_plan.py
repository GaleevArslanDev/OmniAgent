from dataclasses import dataclass, asdict
from typing import Any
import re


OBJECT_ALIASES = {
    "chest": "chest",
    "сундук": "chest",

    "oak_log": "oak_log",
    "дуб": "oak_log",
    "дубовое бревно": "oak_log",
    "дубовый ствол": "oak_log",

    "birch_log": "birch_log",
    "берёза": "birch_log",
    "береза": "birch_log",
    "берёзовое бревно": "birch_log",
    "березовое бревно": "birch_log",

    "spruce_log": "spruce_log",
    "ель": "spruce_log",
    "еловое бревно": "spruce_log",

    "crafting_table": "crafting_table",
    "верстак": "crafting_table",

    "furnace": "furnace",
    "печь": "furnace",
}


@dataclass(slots=True)
class TaskStep:
    id: str
    kind: str
    args: dict[str, Any]

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TaskPlan:
    goal: str
    steps: list[TaskStep]

    def to_json(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "steps": [step.to_json() for step in self.steps],
        }


def resolve_object_name(goal: str) -> str | None:
    lower = goal.lower()

    # Сначала длинные алиасы, чтобы "дубовое бревно"
    # поймалось раньше, чем просто "дуб".
    for alias in sorted(OBJECT_ALIASES.keys(), key=len, reverse=True):
        if alias in lower:
            return OBJECT_ALIASES[alias]

    return None


def extract_seconds(goal: str, default: float = 3.0) -> float:
    lower = goal.lower()

    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(сек|секунд|seconds|second|s)", lower)
    if not match:
        return default

    value = match.group(1).replace(",", ".")
    return float(value)


def parse_task_plan(goal: str) -> TaskPlan:
    """
    v0.5 parser.

    Это НЕ универсальный планнер.
    Это маленький детерминированный распознаватель
    для текущего класса задач:

    - запомнить объект
    - выполнить движение
    - сказать, где был объект

    Если паттерн не распознан, возвращаем пустой план.
    Тогда LLM работает как раньше.
    """
    lower = goal.lower()
    target_name = resolve_object_name(lower)

    wants_remember = (
        "запомни" in lower
        or "запомнить" in lower
        or "помни" in lower
    )

    wants_report = (
        "скажи" in lower
        or "сообщи" in lower
        or "напиши" in lower
    )

    wants_move_forward = (
        "вперёд" in lower
        or "вперед" in lower
        or "пройди" in lower
        or "иди" in lower
    )

    steps: list[TaskStep] = []

    if wants_remember and target_name is not None:
        steps.append(
            TaskStep(
                id="remember_target_location",
                kind="remember_object_location",
                args={
                    "target_name": target_name,
                },
            )
        )

    if wants_move_forward:
        secs = extract_seconds(goal, default=3.0)

        steps.append(
            TaskStep(
                id="move_forward_once",
                kind="use_tool",
                args={
                    "tool": "move_forward",
                    "arguments": {
                        "secs": secs,
                    },
                },
            )
        )

    if wants_report and target_name is not None:
        steps.append(
            TaskStep(
                id="report_target_location",
                kind="report_remembered_location",
                args={
                    "target_name": target_name,
                },
            )
        )

    return TaskPlan(
        goal=goal,
        steps=steps,
    )
