import tempfile
import unittest
from pathlib import Path

from key_macro_studio.executor import MacroExecutor
from key_macro_studio.models import MacroAction, MacroProfile, MacroStep
from key_macro_studio.profile_store import ProfileStore


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


class FakeKeySender:
    def __init__(self) -> None:
        self.events = []

    def press(self, key: str) -> None:
        self.events.append(("press", key))

    def release(self, key: str) -> None:
        self.events.append(("release", key))


class MacroModelTests(unittest.TestCase):
    def test_profile_round_trip_uses_plan_shape(self) -> None:
        profile = MacroProfile(
            name="sample macro",
            startup_delay_seconds=5,
            total_duration_seconds=30,
            stop_hotkey="F12",
            steps=[
                MacroStep("right", MacroAction.TAP, 50),
                MacroStep("shift", MacroAction.PRESS_FOR, 5000),
                MacroStep("ctrl", MacroAction.KEY_DOWN),
                MacroStep("space", MacroAction.PRESS_FOR, 1000),
                MacroStep("ctrl", MacroAction.KEY_UP),
                MacroStep("left", MacroAction.TAP, 50),
            ],
        )

        loaded = MacroProfile.from_dict(profile.to_dict())

        self.assertEqual(loaded.name, "sample macro")
        self.assertEqual(loaded.steps[1].duration_ms, 5000)
        self.assertEqual(loaded.steps[2].action, MacroAction.KEY_DOWN)

    def test_profile_store_import_export(self) -> None:
        profile = MacroProfile(name="stored", steps=[MacroStep("a")])
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "profile.json"
            ProfileStore.export_profile(profile, path)
            imported = ProfileStore.import_profile(path)

        self.assertEqual(imported.name, "stored")
        self.assertEqual(imported.steps[0].key, "a")


class MacroExecutorTests(unittest.TestCase):
    def test_key_specific_durations_press_and_release(self) -> None:
        clock = FakeClock()
        sender = FakeKeySender()
        executor = MacroExecutor(sender, sleep=clock.sleep, monotonic=clock.monotonic)
        profile = MacroProfile(
            startup_delay_seconds=0,
            total_duration_seconds=0,
            steps=[
                MacroStep("shift", MacroAction.PRESS_FOR, 5000),
                MacroStep("right", MacroAction.TAP, 50),
            ],
        )

        result = executor.run(profile)

        self.assertTrue(result.completed)
        self.assertEqual(clock.now, 5.05)
        self.assertEqual(
            sender.events,
            [
                ("press", "shift"),
                ("release", "shift"),
                ("press", "right"),
                ("release", "right"),
            ],
        )

    def test_key_down_is_released_on_finish(self) -> None:
        clock = FakeClock()
        sender = FakeKeySender()
        executor = MacroExecutor(sender, sleep=clock.sleep, monotonic=clock.monotonic)
        profile = MacroProfile(
            startup_delay_seconds=0,
            total_duration_seconds=0,
            steps=[MacroStep("ctrl", MacroAction.KEY_DOWN)],
        )

        executor.run(profile)

        self.assertEqual(sender.events, [("press", "ctrl"), ("release", "ctrl")])

    def test_total_duration_repeats_until_expired(self) -> None:
        clock = FakeClock()
        sender = FakeKeySender()
        executor = MacroExecutor(sender, sleep=clock.sleep, monotonic=clock.monotonic)
        profile = MacroProfile(
            startup_delay_seconds=0,
            total_duration_seconds=0.12,
            steps=[MacroStep("right", MacroAction.TAP, 50)],
        )

        executor.run(profile)

        self.assertEqual(sender.events.count(("press", "right")), 3)
        self.assertAlmostEqual(clock.now, 0.12)

    def test_row_repeat_count_repeats_single_step(self) -> None:
        clock = FakeClock()
        sender = FakeKeySender()
        executor = MacroExecutor(sender, sleep=clock.sleep, monotonic=clock.monotonic)
        profile = MacroProfile(
            startup_delay_seconds=0,
            total_duration_seconds=0,
            steps=[MacroStep("right", MacroAction.TAP, 50, repeat_count=3)],
        )

        executor.run(profile)

        self.assertEqual(sender.events.count(("press", "right")), 3)
        self.assertEqual(sender.events.count(("release", "right")), 3)

    def test_stop_releases_pressed_keys(self) -> None:
        clock = FakeClock()
        sender = FakeKeySender()
        executor = MacroExecutor(sender, sleep=clock.sleep, monotonic=clock.monotonic)

        def stop_after_first_sleep(seconds: float) -> None:
            clock.sleep(seconds)
            executor.request_stop()

        executor.sleep = stop_after_first_sleep
        profile = MacroProfile(
            startup_delay_seconds=0,
            total_duration_seconds=30,
            steps=[MacroStep("shift", MacroAction.PRESS_FOR, 5000)],
        )

        result = executor.run(profile)

        self.assertTrue(result.stopped)
        self.assertEqual(sender.events, [("press", "shift"), ("release", "shift")])


if __name__ == "__main__":
    unittest.main()
