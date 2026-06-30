from dataclasses import dataclass, asdict
from typing import Any

from action import ActionEntry
from task_plan import TaskPlan, TaskStep


@dataclass(slots=True)
class StepProgress:
    step_id: str
    done: bool = False
    evidence: str | None = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


class TaskProgress:
    """
    v0.5 progress tracker.

    Не планнер.
    Не память.
    Не world model.
    Не LLM-written state.

    Это детерминированное состояние выполнения текущего TaskPlan.
    Обновляется только из observation и action log.
    """

    def __init__(self, plan: TaskPlan):
        self.plan = plan

        self.steps: dict[str, StepProgress] = {
            step.id: StepProgress(step_id=step.id)
            for step in plan.steps
        }

        self.remembered_objects: dict[str, dict[str, int]] = {}

    def current_step(self) -> TaskStep | None:
        for step in self.plan.steps:
            progress = self.steps[step.id]
            if not progress.done:
                return step

        return None

    def mark_done(self, step_id: str, evidence: str) -> None:
        if step_id not in self.steps:
            return

        self.steps[step_id].done = True
        self.steps[step_id].evidence = evidence

    def is_done(self) -> bool:
        return bool(self.steps) and all(
            progress.done
            for progress in self.steps.values()
        )

    def update_from_observation(self, observation: dict, step_number: int) -> None:
        current = self.current_step()

        if current is None:
            return

        if current.kind != "remember_object_location":
            return

        target_name = current.args["target_name"]
        nearby = observation.get("vision", {}).get("nearby_objects", [])

        for obj in nearby:
            if obj.get("name") != target_name:
                continue

            pos = {
                "x": obj["x"],
                "y": obj["y"],
                "z": obj["z"],
            }

            self.remembered_objects[target_name] = pos

            self.mark_done(
                current.id,
                (
                    f"{target_name} observed at "
                    f"X={pos['x']}, Y={pos['y']}, Z={pos['z']} "
                    f"on step {step_number}"
                ),
            )
            return

    def update_from_action(self, action: ActionEntry) -> None:
        current = self.current_step()

        if current is None:
            return

        if current.kind == "use_tool":
            self._update_use_tool_step(current, action)
            return

        if current.kind == "report_remembered_location":
            self._update_report_step(current, action)
            return

    def _update_use_tool_step(self, current: TaskStep, action: ActionEntry) -> None:
        expected_tool = current.args["tool"]
        expected_arguments = current.args.get("arguments", {})

        if not action.success:
            return

        if action.tool != expected_tool:
            return

        # v0.5: для move_forward проверяем secs.
        # Позже можно сделать общий matcher аргументов.
        if expected_tool == "move_forward":
            expected_secs = expected_arguments.get("secs")
            actual_secs = action.arguments.get("secs")

            if expected_secs is not None and float(actual_secs) != float(expected_secs):
                return

        self.mark_done(
            current.id,
            f"{expected_tool} succeeded with args={action.arguments} on step {action.step}",
        )

    def _update_report_step(self, current: TaskStep, action: ActionEntry) -> None:
        if not action.success:
            return

        if action.tool != "say":
            return

        target_name = current.args["target_name"]
        text = action.arguments.get("text", "").lower()

        has_target_name = target_name.lower() in text
        has_coordinates = "x=" in text and "y=" in text and "z=" in text

        if not has_target_name and not has_coordinates:
            return

        self.mark_done(
            current.id,
            f"reported remembered location on step {action.step}: {action.arguments.get('text')}",
        )

    def to_json(self) -> dict[str, Any]:
        current = self.current_step()

        return {
            "current_step": current.to_json() if current else None,
            "steps": {
                step_id: progress.to_json()
                for step_id, progress in self.steps.items()
            },
            "remembered_objects": self.remembered_objects,
            "all_done": self.is_done(),
        }