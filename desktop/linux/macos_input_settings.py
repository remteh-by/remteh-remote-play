"""Physical Mac keyboard and five-button mouse bindings for Remote Play.

The wire format deliberately contains only validated integers: it is consumed by
the native input bridge, independent of the currently selected keyboard layout.
This module never reads or writes settings itself.
"""
import math

from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QSlider, QSpinBox, QTabWidget,
    QVBoxLayout, QWidget,
)


ACTION_LABELS = {
    0: ("Cross / A", "Крест / A"),
    1: ("Circle / B", "Круг / B"),
    2: ("Square / X", "Квадрат / X"),
    3: ("Triangle / Y", "Треугольник / Y"),
    4: ("Share / Create", "Share / Create"),
    5: ("PS button", "Кнопка PS"),
    6: ("Options / Menu", "Options / Меню"),
    7: ("L3 · press left stick", "L3 · нажатие левого стика"),
    8: ("R3 · press right stick", "R3 · нажатие правого стика"),
    9: ("L1 / LB", "L1 / LB"),
    10: ("R1 / RB", "R1 / RB"),
    11: ("D-pad ↑", "Крестовина ↑"),
    12: ("D-pad ↓", "Крестовина ↓"),
    13: ("D-pad ←", "Крестовина ←"),
    14: ("D-pad →", "Крестовина →"),
    20: ("Touchpad click", "Нажатие тачпада"),
    21: ("L2 / LT", "L2 / LT"),
    22: ("R2 / RT", "R2 / RT"),
    23: ("Move forward · left stick ↑", "Вперёд · левый стик ↑"),
    24: ("Move backward · left stick ↓", "Назад · левый стик ↓"),
    25: ("Move left · left stick ←", "Влево · левый стик ←"),
    26: ("Move right · left stick →", "Вправо · левый стик →"),
    27: ("Look up · right stick ↑", "Камера вверх · правый стик ↑"),
    28: ("Look down · right stick ↓", "Камера вниз · правый стик ↓"),
    29: ("Look left · right stick ←", "Камера влево · правый стик ←"),
    30: ("Look right · right stick →", "Камера вправо · правый стик →"),
}
KNOWN_ACTIONS = frozenset(ACTION_LABELS) | {-1}
RESERVED_KEYS = frozenset({53, 100, 103, 54, 55, 57, 63})
MODIFIER_ALIASES = {60: 56, 61: 58, 62: 59}
_DEFAULT_KEYBOARD = {
    "13": 23, "1": 24, "0": 25, "2": 26,
    "49": 0, "8": 1, "59": 1, "56": 7, "58": 8,
    "15": 2, "14": 2, "3": 3, "18": 3, "12": 9, "5": 10,
    "126": 11, "125": 12, "123": 13, "124": 14,
    "36": 6, "48": 20, "120": 5, "99": 4,
}
_DEFAULT_MOUSE = [22, 21, 8, 1, 2]
_KEY_NAMES = {
    0: "A", 1: "S", 2: "D", 3: "F", 4: "H", 5: "G", 6: "Z",
    7: "X", 8: "C", 9: "V", 10: "§", 11: "B", 12: "Q", 13: "W",
    14: "E", 15: "R", 16: "Y", 17: "T", 18: "1", 19: "2", 20: "3",
    21: "4", 22: "6", 23: "5", 24: "=", 25: "9", 26: "7", 27: "−",
    28: "8", 29: "0", 30: "]", 31: "O", 32: "U", 33: "[", 34: "I",
    35: "P", 36: "Enter", 37: "L", 38: "J", 39: "'", 40: "K", 41: ";",
    42: "\\", 43: ",", 44: "/", 45: "N", 46: "M", 47: ".", 48: "Tab",
    49: "Space", 50: "`", 51: "Backspace", 56: "Shift", 58: "Option / Alt",
    59: "Control", 64: "F17", 65: "Num .", 67: "Num *", 69: "Num +",
    71: "Num Clear", 75: "Num /", 76: "Num Enter", 78: "Num −",
    79: "F18", 80: "F19", 81: "Num =", 82: "Num 0", 83: "Num 1",
    84: "Num 2", 85: "Num 3", 86: "Num 4", 87: "Num 5", 88: "Num 6",
    89: "Num 7", 91: "Num 8", 92: "Num 9", 96: "F5", 97: "F6",
    98: "F7", 99: "F3", 101: "F9", 105: "F13", 106: "F16",
    107: "F14", 109: "F10", 111: "F12", 113: "F15", 114: "Help",
    115: "Home", 116: "Page Up", 117: "Delete", 118: "F4", 119: "End",
    120: "F2", 121: "Page Down", 122: "F1", 123: "←", 124: "→",
    125: "↓", 126: "↑",
}


def default_bindings():
    """Return an independent default configuration, safe to edit."""
    return {"keyboard": dict(_DEFAULT_KEYBOARD), "mouse": list(_DEFAULT_MOUSE)}


def _key_code(value):
    if type(value) is int:
        code = value
    elif isinstance(value, str) and value.isascii() and value.isdecimal():
        try:
            code = int(value)
        except ValueError:
            return None
    else:
        return None
    if not 0 <= code <= 127 or code in RESERVED_KEYS:
        return None
    return MODIFIER_ALIASES.get(code, code)


def normalize_bindings(value):
    """Validate persisted settings without retaining references to caller data.

    An explicitly empty keyboard mapping disables keyboard actions. Bad entries
    are discarded; a missing/malformed section uses defaults. Canonical left
    modifiers beat their right-hand aliases, independent of JSON key order.
    At most two physical keys are retained per action, in numeric key order.
    """
    result = default_bindings()
    if not isinstance(value, dict):
        return result
    keyboard = value.get("keyboard")
    if isinstance(keyboard, dict):
        candidates = []
        for raw_code, action in keyboard.items():
            code = _key_code(raw_code)
            if code is not None and type(action) is int and action in KNOWN_ACTIONS:
                candidates.append((int(raw_code) != code, int(raw_code), code, action))
        canonical = {}
        for _, _, code, action in sorted(candidates):
            canonical.setdefault(code, action)
        result["keyboard"] = {}
        counts = {}
        for code, action in sorted(canonical.items()):
            if action != -1 and counts.get(action, 0) < 2:
                result["keyboard"][str(code)] = action
                counts[action] = counts.get(action, 0) + 1
    mouse = value.get("mouse")
    if isinstance(mouse, (list, tuple)) and len(mouse) == 5:
        result["mouse"] = [
            action if type(action) is int and action in KNOWN_ACTIONS else _DEFAULT_MOUSE[i]
            for i, action in enumerate(mouse)
        ]
    return result


def encode_bindings(value):
    """Native bridge environment format; no arbitrary text crosses this boundary."""
    bindings = normalize_bindings(value)
    keyboard = ",".join(f"{code}:{action}" for code, action in sorted(
        bindings["keyboard"].items(), key=lambda item: int(item[0])))
    mouse = ",".join(f"{index}:{action}" for index, action in enumerate(bindings["mouse"]))
    return keyboard, mouse


class _KeyCaptureDialog(QDialog):
    def __init__(self, translate, parent=None, key_decoder=None):
        super().__init__(parent)
        self._tr = translate
        self.language=getattr(parent,'language','en')
        self._key_decoder = key_decoder or (lambda event:_key_code(event.nativeVirtualKey()))
        self.key_code = None
        self.setWindowTitle(translate("Assign a key", "Назначить клавишу"))
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        from i18n import text
        self.hint = QLabel(text('press_key',self.language))
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)
        cancel = QPushButton(translate("Cancel", "Отмена"))
        cancel.clicked.connect(self.reject)
        cancel.installEventFilter(self)
        layout.addWidget(cancel)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.ShortcutOverride, QEvent.KeyPress):
            return self.event(event)
        return super().eventFilter(watched, event)

    def event(self, event):
        # Catch Tab before QDialog turns it into focus traversal. ShortcutOverride
        # also prevents a focused button or ancestor shortcut consuming the key.
        if event.type() == QEvent.ShortcutOverride:
            event.accept()
            return True
        if event.type() == QEvent.KeyPress:
            if event.isAutoRepeat():
                return True
            if event.key() == Qt.Key_Escape:
                self.reject()
                return True
            code = self._key_decoder(event)
            if code is None:
                from i18n import text
                self.hint.setText(text('editor_reserved',self.language))
                return True
            self.key_code = code
            self.accept()
            return True
        return super().event(event)


class InputSettingsDialog(QDialog):
    """Edit bindings in memory; callers persist result_values() only on Accept."""

    def __init__(self, preferences, language, parent=None, platform='macos'):
        super().__init__(parent)
        self._russian = str(language).lower().startswith("ru")
        self.language=language
        self.platform=platform
        if platform=='linux':
            import linux_input_settings as codec
            self._normalize=codec.normalize_bindings;self._defaults=codec.default_bindings
            self._key_code=codec.key_code;self._names=codec.NAMES;self._capture=codec.capture_code
        else:
            self._normalize=normalize_bindings;self._defaults=default_bindings
            self._key_code=_key_code;self._names=_KEY_NAMES;self._capture=None
        preferences = preferences if isinstance(preferences, dict) else {}
        self._bindings = self._normalize(preferences.get("input_bindings" if platform=='macos' else 'linux_input_bindings'))
        self._key_buttons = {}
        self.setWindowTitle(self._tr("Keyboard & mouse", "Клавиатура и мышь"))
        self.resize(810, 720)
        self.setMinimumSize(620, 470)
        self.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #303640; border-radius: 10px; }
            QTabBar::tab { padding: 12px 22px; color: #A4ACBA; }
            QTabBar::tab:selected { color: #DAF975; background: #222730; }
            QPushButton#bindingKey { padding: 6px 8px; min-height: 20px; }
            QPushButton#bindingClear { padding: 4px; min-height: 20px; }
            QSlider::groove:horizontal { height: 6px; background: #303640; border-radius: 3px; }
            QSlider::handle:horizontal { width: 18px; margin: -6px 0; border-radius: 9px; background: #DAF975; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(14)
        title = QLabel(self._tr("Make every input yours", "Управление под вас"))
        title.setObjectName("heading")
        layout.addWidget(title)
        from i18n import text
        description = QLabel(text('editor_help',language))
        description.setWordWrap(True)
        description.setObjectName("muted")
        layout.addWidget(description)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        self._build_keyboard_tab()
        self._build_mouse_tab()
        self.status = QLabel(text('input_mode_keyboard',language))
        self.status.setWordWrap(True)
        self.status.setObjectName("small")
        layout.addWidget(self.status)
        footer = QHBoxLayout()
        restore = QPushButton(self._tr("Restore defaults", "По умолчанию"))
        restore.clicked.connect(self._restore_defaults)
        footer.addWidget(restore)
        footer.addStretch()
        buttons = QDialogButtonBox()
        buttons.addButton(self._tr("Cancel", "Отмена"), QDialogButtonBox.RejectRole)
        save = buttons.addButton(self._tr("Save", "Сохранить"), QDialogButtonBox.AcceptRole)
        save.setObjectName("primary")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        footer.addWidget(buttons)
        layout.addLayout(footer)
        raw_sensitivity = preferences.get("mouse_sensitivity", 0.025)
        try:
            sensitivity = float(raw_sensitivity)
            if isinstance(raw_sensitivity, bool) or not math.isfinite(sensitivity):
                sensitivity = 0.025
        except (TypeError, ValueError, OverflowError):
            sensitivity = 0.025
        self.speed_spin.setValue(round(min(0.2, max(0.001, sensitivity)) / 0.025 * 100))
        self.invert_check.setChecked(preferences.get("invert_mouse_y") is True)
        self._refresh_keys()

    def _tr(self, english, russian):
        from i18n import pair
        return pair(english,russian,self.language)

    def _action_name(self, action):
        return {0:'✕ / A',1:'○ / B',2:'□ / X',3:'△ / Y',4:'Share / Create',5:'PS',6:'Options / Menu',7:'L3',8:'R3',9:'L1 / LB',10:'R1 / RB',11:'D-pad ↑',12:'D-pad ↓',13:'D-pad ←',14:'D-pad →',20:'Touchpad',21:'L2 / LT',22:'R2 / RT',23:'LS ↑',24:'LS ↓',25:'LS ←',26:'LS →',27:'RS ↑',28:'RS ↓',29:'RS ←',30:'RS →'}[action]

    def _build_keyboard_tab(self):
        container = QWidget()
        grid = QGridLayout(container)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(0, 1)
        for column, label in ((0, self._tr("Controller action", "Действие геймпада")),
                              (1, self._tr("Key 1", "Клавиша 1")),
                              (3, self._tr("Key 2", "Клавиша 2"))):
            header = QLabel(label)
            header.setObjectName("muted")
            grid.addWidget(header, 0, column)
        ordered_actions = [23, 24, 25, 26, 0, 1, 2, 3, 9, 10, 21, 22, 7, 8,
                           11, 12, 13, 14, 6, 20, 5, 4, 27, 28, 29, 30]
        for row, action in enumerate(ordered_actions, 1):
            grid.addWidget(QLabel(self._action_name(action)), row, 0)
            for slot in range(2):
                key_button = QPushButton()
                key_button.setObjectName("bindingKey")
                key_button.setMinimumWidth(100)
                key_button.setAccessibleName(self._tr("Assign a key", "Назначить клавишу")+': ' + self._action_name(action))
                key_button.clicked.connect(lambda checked=False, a=action, s=slot: self._capture_key(a, s))
                clear_button = QPushButton("×")
                clear_button.setObjectName("bindingClear")
                clear_button.setFixedWidth(28)
                clear_button.setToolTip(self._tr("Clear this key", "Убрать назначение"))
                clear_button.setAccessibleName(self._tr("Clear this key", "Убрать назначение")+': ' + self._action_name(action))
                clear_button.clicked.connect(lambda checked=False, a=action, s=slot: self._clear_key(a, s))
                grid.addWidget(key_button, row, 1 + 2 * slot)
                grid.addWidget(clear_button, row, 2 + 2 * slot)
                self._key_buttons[(action, slot)] = (key_button, clear_button)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        self.tabs.addTab(scroll, self._tr("Keyboard", "Клавиатура"))

    def _build_mouse_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        self.mouse_combos = []
        names = [("Left button", "Левая кнопка"), ("Right button", "Правая кнопка"),
                 ("Middle / wheel click", "Средняя / нажатие колеса"),
                 ("Side button 1 · Back", "Боковая кнопка 1 · Назад"),
                 ("Side button 2 · Forward", "Боковая кнопка 2 · Вперёд")]
        for index, name in enumerate(names):
            caption = QLabel(self._tr(*name))
            combo = QComboBox()
            combo.setAccessibleName(self._tr(*name))
            combo.addItem(self._tr("Unassigned", "Не назначено"), -1)
            for action in ACTION_LABELS:
                combo.addItem(self._action_name(action), action)
            combo.setCurrentIndex(combo.findData(self._bindings["mouse"][index]))
            caption.setBuddy(combo)
            grid.addWidget(caption, index, 0)
            grid.addWidget(combo, index, 1)
            self.mouse_combos.append(combo)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)
        layout.addSpacing(16)
        speed_label = QLabel(self._tr("Mouse speed", "Скорость мыши"))
        speed_label.setObjectName("heading")
        layout.addWidget(speed_label)
        speed_row = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(4, 800)
        self.speed_slider.setAccessibleName(self._tr("Mouse speed", "Скорость мыши"))
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(4, 800)
        self.speed_spin.setSuffix(" %")
        self.speed_spin.setAccessibleName(self._tr("Mouse speed percent", "Скорость мыши в процентах"))
        self.speed_slider.valueChanged.connect(self.speed_spin.setValue)
        self.speed_spin.valueChanged.connect(self.speed_slider.setValue)
        speed_row.addWidget(self.speed_slider, 1)
        speed_row.addWidget(self.speed_spin)
        layout.addLayout(speed_row)
        from i18n import text
        info = QLabel(text('keyboard_mouse',self.language)+' · 100% · ΔX / ΔY → RS')
        info.setWordWrap(True)
        info.setObjectName("muted")
        layout.addWidget(info)
        self.invert_check = QCheckBox(self._tr("Invert vertical mouse movement", "Инвертировать движение мыши по вертикали"))
        layout.addWidget(self.invert_check)
        layout.addStretch()
        self.tabs.addTab(page, self._tr("Mouse", "Мышь"))

    def _keys_for_action(self, action):
        return sorted(int(code) for code, assigned in self._bindings["keyboard"].items() if assigned == action)

    def _refresh_keys(self):
        for (action, slot), (button, clear) in self._key_buttons.items():
            keys = self._keys_for_action(action)
            code = keys[slot] if slot < len(keys) else None
            button.setText(self._names.get(code, f"Key {code}") if code is not None else self._tr("Assign…", "Назначить…"))
            clear.setEnabled(code is not None)

    def _clear_key(self, action, slot):
        keys = self._keys_for_action(action)
        if slot < len(keys):
            self._bindings["keyboard"].pop(str(keys[slot]), None)
        self._refresh_keys()

    def _capture_key(self, action, slot):
        capture = _KeyCaptureDialog(self._tr, self, self._capture)
        if capture.exec_() == QDialog.Accepted and capture.key_code is not None:
            self._assign_key(action, slot, capture.key_code)

    def _assign_key(self, action, slot, raw_code):
        code = self._key_code(raw_code)
        if code is None or action not in ACTION_LABELS or slot not in (0, 1):
            return
        keys = self._keys_for_action(action)
        previous_action = self._bindings["keyboard"].get(str(code))
        if slot < len(keys):
            self._bindings["keyboard"].pop(str(keys[slot]), None)
        self._bindings["keyboard"][str(code)] = action
        if previous_action is not None and previous_action != action:
            from i18n import text
            self.status.setText(text('binding_moved',self.language,key=self._names.get(code,str(code)),old=self._action_name(previous_action),new=self._action_name(action)))
        self._refresh_keys()

    def _restore_defaults(self):
        self._bindings = self._defaults()
        for combo, action in zip(self.mouse_combos, self._bindings["mouse"]):
            combo.setCurrentIndex(combo.findData(action))
        self.speed_spin.setValue(100)
        self.invert_check.setChecked(False)
        from i18n import text
        self.status.setText(text('defaults_restored',self.language))
        self._refresh_keys()

    def result_values(self):
        return {
            ("input_bindings" if self.platform=='macos' else 'linux_input_bindings'): self._normalize({
                "keyboard": self._bindings["keyboard"],
                "mouse": [combo.currentData() for combo in self.mouse_combos],
            }),
            "mouse_sensitivity": self.speed_spin.value() * 0.025 / 100,
            "invert_mouse_y": self.invert_check.isChecked(),
            "keyboard_mouse": True,
        }
