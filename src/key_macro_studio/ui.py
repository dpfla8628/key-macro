from __future__ import annotations

import sys
from pathlib import Path

from .executor import MacroExecutor, StopHotkeyListener
from .keymap import KEYBOARD_ROWS, display_key_name
from .models import ACTION_LABELS, LABEL_TO_ACTION, MacroAction, MacroProfile, MacroStep
from .profile_store import ProfileStore

try:
    from PySide6.QtCore import QObject, Qt, QTimer, Signal
    from PySide6.QtWidgets import (
        QApplication,
        QAbstractItemView,
        QComboBox,
        QFileDialog,
        QFormLayout,
        QGridLayout,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QSpinBox,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - exercised by users without deps.
    raise SystemExit(
        "PySide6 is not installed. Run: python -m pip install -r requirements.txt"
    ) from exc


class UiBridge(QObject):
    status = Signal(str)
    stop_requested = Signal()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Key Macro Studio")
        self.resize(1180, 760)
        self.store = ProfileStore()
        self.profiles = self.store.load_all()
        self.executor: MacroExecutor | None = None
        self.hotkey_listener: StopHotkeyListener | None = None
        self._running = False

        self.name_edit = QLineEdit("New Macro")
        self.start_delay = QSpinBox()
        self.start_delay.setRange(0, 120)
        self.start_delay.setValue(5)
        self.total_duration = QSpinBox()
        self.total_duration.setRange(0, 86400)
        self.total_duration.setValue(30)
        self.stop_hotkey = QLineEdit("F12")
        self.status_label = QLabel("준비됨")
        self.bridge = UiBridge()
        self.bridge.status.connect(self.status_label.setText)
        self.bridge.stop_requested.connect(self.stop_macro)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["키", "동작", "시간(ms)", "반복"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)

        self._build()
        if self.profiles:
            self.load_profile(self.profiles[0])

    def _build(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)

        form = QFormLayout()
        form.addRow("프로필", self.name_edit)
        form.addRow("시작 전 대기(초)", self.start_delay)
        form.addRow("전체 실행시간(초, 0=1회)", self.total_duration)
        form.addRow("중지 키", self.stop_hotkey)
        layout.addLayout(form)

        keyboard = QGridLayout()
        for row_index, row in enumerate(KEYBOARD_ROWS):
            col = 0
            for key, label in row:
                button = QPushButton(label)
                button.setMinimumHeight(38)
                button.clicked.connect(lambda checked=False, key=key: self.add_step(key))
                span = 3 if key == "space" else 2 if key in {"shift", "enter", "backspace"} else 1
                keyboard.addWidget(button, row_index, col, 1, span)
                col += span
        layout.addLayout(keyboard)

        layout.addWidget(self.table)

        table_buttons = QHBoxLayout()
        add_delay = QPushButton("대기 추가")
        add_delay.clicked.connect(self.add_delay_step)
        move_up = QPushButton("위로")
        move_up.clicked.connect(lambda: self.move_selected(-1))
        move_down = QPushButton("아래로")
        move_down.clicked.connect(lambda: self.move_selected(1))
        remove = QPushButton("삭제")
        remove.clicked.connect(self.remove_selected)
        for button in [add_delay, move_up, move_down, remove]:
            table_buttons.addWidget(button)
        layout.addLayout(table_buttons)

        buttons = QHBoxLayout()
        run = QPushButton("실행")
        run.clicked.connect(self.run_macro)
        stop = QPushButton("중지")
        stop.clicked.connect(self.stop_macro)
        save = QPushButton("저장")
        save.clicked.connect(self.save_current_profile)
        import_button = QPushButton("JSON 가져오기")
        import_button.clicked.connect(self.import_profile)
        export_button = QPushButton("JSON 내보내기")
        export_button.clicked.connect(self.export_profile)
        for button in [run, stop, save, import_button, export_button]:
            buttons.addWidget(button)
        layout.addLayout(buttons)

        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        self.setCentralWidget(root)

    def add_step(self, key: str) -> None:
        self._append_step(MacroStep(key=key, action=MacroAction.TAP, duration_ms=50))

    def add_delay_step(self) -> None:
        self._append_step(MacroStep(action=MacroAction.DELAY, duration_ms=1000))

    def _append_step(self, step: MacroStep) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        key_item = QTableWidgetItem(display_key_name(step.key) if step.key else "")
        key_item.setData(Qt.UserRole, step.key)
        self.table.setItem(row, 0, key_item)

        action_combo = QComboBox()
        for action, label in ACTION_LABELS.items():
            action_combo.addItem(label, action.value)
        action_combo.setCurrentText(ACTION_LABELS[step.action])
        self.table.setCellWidget(row, 1, action_combo)

        duration = QSpinBox()
        duration.setRange(0, 86_400_000)
        duration.setValue(step.duration_ms)
        self.table.setCellWidget(row, 2, duration)

        repeat = QSpinBox()
        repeat.setRange(1, 9999)
        repeat.setValue(step.repeat_count)
        self.table.setCellWidget(row, 3, repeat)

    def move_selected(self, direction: int) -> None:
        row = self.table.currentRow()
        target = row + direction
        if row < 0 or target < 0 or target >= self.table.rowCount():
            return
        steps = self.steps_from_table()
        steps[row], steps[target] = steps[target], steps[row]
        self.populate_steps(steps)
        self.table.selectRow(target)

    def remove_selected(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def steps_from_table(self) -> list[MacroStep]:
        steps: list[MacroStep] = []
        for row in range(self.table.rowCount()):
            key_item = self.table.item(row, 0)
            key = str(key_item.data(Qt.UserRole) or "") if key_item else ""
            action_combo = self.table.cellWidget(row, 1)
            duration_spin = self.table.cellWidget(row, 2)
            repeat_spin = self.table.cellWidget(row, 3)
            action = MacroAction(action_combo.currentData())
            duration = duration_spin.value()
            repeat_count = repeat_spin.value()
            steps.append(MacroStep(key=key, action=action, duration_ms=duration, repeat_count=repeat_count))
        return steps

    def populate_steps(self, steps: list[MacroStep]) -> None:
        self.table.setRowCount(0)
        for step in steps:
            self._append_step(step)

    def current_profile(self) -> MacroProfile:
        return MacroProfile(
            name=self.name_edit.text(),
            startup_delay_seconds=self.start_delay.value(),
            total_duration_seconds=self.total_duration.value(),
            stop_hotkey=self.stop_hotkey.text(),
            steps=self.steps_from_table(),
        ).normalized()

    def load_profile(self, profile: MacroProfile) -> None:
        profile = profile.normalized()
        self.name_edit.setText(profile.name)
        self.start_delay.setValue(int(profile.startup_delay_seconds))
        self.total_duration.setValue(int(profile.total_duration_seconds))
        self.stop_hotkey.setText(profile.stop_hotkey)
        self.populate_steps(profile.steps)

    def save_current_profile(self) -> None:
        profile = self.current_profile()
        self.profiles = [item for item in self.profiles if item.name != profile.name]
        self.profiles.append(profile)
        self.store.save_all(self.profiles)
        self.status_label.setText("저장됨")

    def import_profile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "프로필 가져오기", "", "JSON (*.json)")
        if not path:
            return
        try:
            profile = ProfileStore.import_profile(Path(path))
            self.load_profile(profile)
            self.status_label.setText("가져오기 완료")
        except Exception as exc:
            QMessageBox.critical(self, "가져오기 실패", str(exc))

    def export_profile(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "프로필 내보내기", f"{self.name_edit.text()}.json", "JSON (*.json)")
        if not path:
            return
        try:
            ProfileStore.export_profile(self.current_profile(), Path(path))
            self.status_label.setText("내보내기 완료")
        except Exception as exc:
            QMessageBox.critical(self, "내보내기 실패", str(exc))

    def run_macro(self) -> None:
        if self._running:
            return
        profile = self.current_profile()
        if not profile.steps:
            QMessageBox.warning(self, "실행 불가", "매크로 단계가 없습니다.")
            return
        try:
            self._running = True
            self.executor = MacroExecutor(status_callback=self.bridge.status.emit)
            self.hotkey_listener = StopHotkeyListener(profile.stop_hotkey, self.bridge.stop_requested.emit)
            self.hotkey_listener.start()
            thread = self.executor.start_thread(profile)
            QTimer.singleShot(100, lambda: self._watch_thread(thread))
        except Exception as exc:
            self._running = False
            QMessageBox.critical(self, "실행 실패", str(exc))

    def stop_macro(self) -> None:
        if self.executor:
            self.executor.request_stop()
        self.status_label.setText("중지 요청됨")

    def _watch_thread(self, thread) -> None:
        if thread.is_alive():
            QTimer.singleShot(100, lambda: self._watch_thread(thread))
            return
        self._running = False
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
