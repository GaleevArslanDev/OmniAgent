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


def wants_remember(goal: str) -> bool:
    lower = goal.lower()

    return (
        "запомни" in lower
        or "запомнить" in lower
        or "помни" in lower
    )


def wants_report(goal: str) -> bool:
    lower = goal.lower()

    return (
        "скажи" in lower
        or "сообщи" in lower
        or "напиши" in lower
    )


def wants_move_forward(goal: str) -> bool:
    lower = goal.lower()

    return (
        "вперёд" in lower
        or "вперед" in lower
        or "пройди" in lower
        or "иди" in lower
    )


def wants_dig(goal: str) -> bool:
    lower = goal.lower()

    return (
        "сломай" in lower
        or "сломать" in lower
        or "добудь" in lower
        or "добыть" in lower
        or "разбей" in lower
        or "вскопать" in lower
        or "вскопай" in lower
    )


def wants_change_report(goal: str) -> bool:
    lower = goal.lower()

    return (
        "что изменилось" in lower
        or "изменилось" in lower
        or "скажи" in lower
        or "сообщи" in lower
        or "напиши" in lower
    )


def try_parse_remember_move_report(goal: str) -> TaskPlan | None:
    target_name = resolve_object_name(goal)

    if target_name is None:
        return None

    if not wants_remember(goal):
        return None

    steps: list[TaskStep] = []

    steps.append(
        TaskStep(
            id="remember_target_location",
            kind="remember_object_location",
            args={
                "target_name": target_name,
            },
        )
    )

    if wants_move_forward(goal):
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

    if wants_report(goal):
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


def try_parse_dig_object(goal: str) -> TaskPlan | None:
    target_name = resolve_object_name(goal)

    if target_name is None:
        return None

    if not wants_dig(goal):
        return None

    steps: list[TaskStep] = [
        TaskStep(
            id="look_at_target",
            kind="use_tool",
            args={
                "tool": "look_at_nearest",
                "arguments": {
                    "block_name": target_name,
                },
            },
        ),
        TaskStep(
            id="dig_target",
            kind="use_tool",
            args={
                "tool": "dig_block_at_cursor",
                "arguments": {
                    "expected_name": target_name,
                },
            },
        ),
    ]

    if wants_change_report(goal):
        steps.append(
            TaskStep(
                id="report_change",
                kind="report_observation_diff",
                args={
                    "target_name": target_name,
                },
            )
        )

    return TaskPlan(
        goal=goal,
        steps=steps,
    )


def parse_task_plan(goal: str) -> TaskPlan:
    """
    v0.6 parser.

    Это НЕ универсальный планнер.
    Это набор маленьких детерминированных распознавателей известных шаблонов.

    Сейчас поддерживаются:

    1. remember/move/report:
       "Запомни chest, пройди вперёд 3 секунды, скажи где был chest"

    2. dig/report-diff:
       "Повернись к oak_log, сломай его, скажи что изменилось"

    Смешанные команды с несколькими разными целями пока лучше не поддерживать.
    Если паттерн не распознан, возвращаем пустой план.
    Тогда LLM работает как раньше.
    """
    parsers = [
        try_parse_remember_move_report,
        try_parse_dig_object,
    ]

    for parser in parsers:
        plan = parser(goal)
        if plan is not None and plan.steps:
            return plan

    return TaskPlan(
        goal=goal,
        steps=[],
    )