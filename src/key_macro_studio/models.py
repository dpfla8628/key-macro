from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MacroAction(str, Enum):
    TAP = "tap"
    PRESS_FOR = "press_for"
    KEY_DOWN = "key_down"
    KEY_UP = "key_up"
    DELAY = "delay"
    REPEAT = "repeat"


ACTION_LABELS = {
    MacroAction.TAP: "클릭",
    MacroAction.PRESS_FOR: "유지",
    MacroAction.KEY_DOWN: "누른 상태 유지",
    MacroAction.KEY_UP: "떼기",
    MacroAction.DELAY: "대기",
    MacroAction.REPEAT: "반복",
}

LABEL_TO_ACTION = {label: action for action, label in ACTION_LABELS.items()}


@dataclass(slots=True)
class MacroStep:
    key: str = ""
    action: MacroAction = MacroAction.TAP
    duration_ms: int = 50
    repeat_count: int = 1
    steps: list["MacroStep"] = field(default_factory=list)

    def normalized(self) -> "MacroStep":
        duration = max(0, int(self.duration_ms))
        repeat_count = max(1, int(self.repeat_count))
        key = "" if self.action in {MacroAction.DELAY, MacroAction.REPEAT} else self.key
        return MacroStep(
            key=key,
            action=self.action,
            duration_ms=duration,
            repeat_count=repeat_count,
            steps=[step.normalized() for step in self.steps],
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "key": self.key,
            "action": self.action.value,
        }
        if self.action in {MacroAction.TAP, MacroAction.PRESS_FOR, MacroAction.DELAY}:
            data["durationMs"] = self.duration_ms
        if self.action == MacroAction.REPEAT:
            data["repeatCount"] = self.repeat_count
            data["steps"] = [step.to_dict() for step in self.steps]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MacroStep":
        raw_action = data.get("action", MacroAction.TAP.value)
        action = MacroAction(raw_action)
        return cls(
            key=str(data.get("key", "")),
            action=action,
            duration_ms=int(data.get("durationMs", 50 if action == MacroAction.TAP else 0)),
            repeat_count=int(data.get("repeatCount", 1)),
            steps=[cls.from_dict(step) for step in data.get("steps", [])],
        ).normalized()


@dataclass(slots=True)
class MacroProfile:
    name: str = "New Macro"
    startup_delay_seconds: float = 5.0
    total_duration_seconds: float = 30.0
    stop_hotkey: str = "F12"
    steps: list[MacroStep] = field(default_factory=list)

    def normalized(self) -> "MacroProfile":
        return MacroProfile(
            name=self.name.strip() or "New Macro",
            startup_delay_seconds=max(0.0, float(self.startup_delay_seconds)),
            total_duration_seconds=max(0.0, float(self.total_duration_seconds)),
            stop_hotkey=self.stop_hotkey.strip() or "F12",
            steps=[step.normalized() for step in self.steps],
        )

    def to_dict(self) -> dict[str, Any]:
        profile = self.normalized()
        return {
            "name": profile.name,
            "startupDelaySeconds": profile.startup_delay_seconds,
            "totalDurationSeconds": profile.total_duration_seconds,
            "stopHotkey": profile.stop_hotkey,
            "steps": [step.to_dict() for step in profile.steps],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MacroProfile":
        return cls(
            name=str(data.get("name", "New Macro")),
            startup_delay_seconds=float(data.get("startupDelaySeconds", 5.0)),
            total_duration_seconds=float(data.get("totalDurationSeconds", 30.0)),
            stop_hotkey=str(data.get("stopHotkey", "F12")),
            steps=[MacroStep.from_dict(step) for step in data.get("steps", [])],
        ).normalized()
