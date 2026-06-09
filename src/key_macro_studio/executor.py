from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from .keymap import pynput_key_for
from .models import MacroAction, MacroProfile, MacroStep

StatusCallback = Callable[[str], None]


class KeySender(Protocol):
    def press(self, key: str) -> None:
        ...

    def release(self, key: str) -> None:
        ...


class PynputKeySender:
    def __init__(self) -> None:
        from pynput.keyboard import Controller

        self._controller = Controller()

    def press(self, key: str) -> None:
        self._controller.press(pynput_key_for(key))

    def release(self, key: str) -> None:
        self._controller.release(pynput_key_for(key))


@dataclass(slots=True)
class ExecutionResult:
    completed: bool
    stopped: bool
    message: str


class MacroExecutor:
    def __init__(
        self,
        key_sender: KeySender | None = None,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
        status_callback: StatusCallback | None = None,
    ) -> None:
        self.key_sender = key_sender or PynputKeySender()
        self.sleep = sleep
        self.monotonic = monotonic
        self.status_callback = status_callback
        self.stop_event = threading.Event()
        self._pressed_keys: set[str] = set()
        self._thread: threading.Thread | None = None

    def request_stop(self) -> None:
        self.stop_event.set()

    def reset_stop(self) -> None:
        self.stop_event.clear()

    def start_thread(self, profile: MacroProfile) -> threading.Thread:
        if self._thread and self._thread.is_alive():
            raise RuntimeError("Macro is already running")
        self.reset_stop()
        self._thread = threading.Thread(target=self.run, args=(profile,), daemon=True)
        self._thread.start()
        return self._thread

    def run(self, profile: MacroProfile) -> ExecutionResult:
        profile = profile.normalized()
        try:
            if not profile.steps:
                return ExecutionResult(False, False, "No macro steps to run.")
            self._status("카운트다운 시작")
            if not self._interruptible_sleep(profile.startup_delay_seconds):
                return ExecutionResult(False, True, "Stopped during countdown.")

            self._status("실행 중")
            deadline = None
            if profile.total_duration_seconds > 0:
                deadline = self.monotonic() + profile.total_duration_seconds

            while not self.stop_event.is_set():
                if deadline is not None and self.monotonic() >= deadline:
                    break
                self._run_steps(profile.steps, deadline)
                if deadline is None:
                    break

            stopped = self.stop_event.is_set()
            return ExecutionResult(not stopped, stopped, "Stopped." if stopped else "Completed.")
        finally:
            self.release_all()
            self._status("중지됨" if self.stop_event.is_set() else "완료됨")

    def release_all(self) -> None:
        for key in list(self._pressed_keys):
            self._release(key)

    def _run_steps(self, steps: list[MacroStep], deadline: float | None) -> None:
        for step in steps:
            if self.stop_event.is_set() or self._deadline_passed(deadline):
                return
            step = step.normalized()
            for _ in range(step.repeat_count):
                if self.stop_event.is_set() or self._deadline_passed(deadline):
                    return
                if step.action == MacroAction.REPEAT:
                    self._run_steps(step.steps, deadline)
                else:
                    self._run_step(step, deadline)

    def _run_step(self, step: MacroStep, deadline: float | None) -> None:
        if step.action == MacroAction.TAP:
            self._press(step.key)
            self._interruptible_sleep_ms(step.duration_ms, deadline)
            self._release(step.key)
        elif step.action == MacroAction.PRESS_FOR:
            self._press(step.key)
            self._interruptible_sleep_ms(step.duration_ms, deadline)
            self._release(step.key)
        elif step.action == MacroAction.KEY_DOWN:
            self._press(step.key)
        elif step.action == MacroAction.KEY_UP:
            self._release(step.key)
        elif step.action == MacroAction.DELAY:
            self._interruptible_sleep_ms(step.duration_ms, deadline)

    def _press(self, key: str) -> None:
        if not key:
            return
        self.key_sender.press(key)
        self._pressed_keys.add(key)

    def _release(self, key: str) -> None:
        if not key:
            return
        try:
            self.key_sender.release(key)
        finally:
            self._pressed_keys.discard(key)

    def _interruptible_sleep_ms(self, duration_ms: int, deadline: float | None) -> bool:
        seconds = max(0.0, duration_ms / 1000)
        if deadline is not None:
            seconds = min(seconds, max(0.0, deadline - self.monotonic()))
        return self._interruptible_sleep(seconds)

    def _interruptible_sleep(self, seconds: float) -> bool:
        end_time = self.monotonic() + max(0.0, seconds)
        while not self.stop_event.is_set():
            remaining = end_time - self.monotonic()
            if remaining <= 0:
                return True
            self.sleep(min(remaining, 0.05))
        return False

    def _deadline_passed(self, deadline: float | None) -> bool:
        return deadline is not None and self.monotonic() >= deadline

    def _status(self, message: str) -> None:
        if self.status_callback:
            self.status_callback(message)


class StopHotkeyListener:
    def __init__(self, hotkey: str, callback: Callable[[], None]) -> None:
        self.hotkey = hotkey
        self.callback = callback
        self._listener = None

    def start(self) -> None:
        from pynput import keyboard

        key_name = self.hotkey.lower()

        def on_press(key) -> None:
            if self._matches(key, key_name):
                self.callback()

        self._listener = keyboard.Listener(on_press=on_press)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener = None

    @staticmethod
    def _matches(key, key_name: str) -> bool:
        try:
            return key.name.lower() == key_name.lower()
        except AttributeError:
            return False
