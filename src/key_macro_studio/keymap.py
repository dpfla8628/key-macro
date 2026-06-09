from __future__ import annotations

SPECIAL_KEY_NAMES = {
    "backspace",
    "caps_lock",
    "cmd",
    "ctrl",
    "delete",
    "down",
    "end",
    "enter",
    "esc",
    "f1",
    "f2",
    "f3",
    "f4",
    "f5",
    "f6",
    "f7",
    "f8",
    "f9",
    "f10",
    "f11",
    "f12",
    "home",
    "left",
    "option",
    "page_down",
    "page_up",
    "right",
    "shift",
    "space",
    "tab",
    "up",
}

DISPLAY_NAMES = {
    "backspace": "Backspace",
    "caps_lock": "Caps",
    "cmd": "Cmd",
    "ctrl": "Ctrl",
    "delete": "Del",
    "down": "↓",
    "end": "End",
    "enter": "Enter",
    "esc": "Esc",
    "home": "Home",
    "left": "←",
    "option": "Alt/Opt",
    "page_down": "PgDn",
    "page_up": "PgUp",
    "right": "→",
    "shift": "Shift",
    "space": "Space",
    "tab": "Tab",
    "up": "↑",
}

KEYBOARD_ROWS: list[list[tuple[str, str]]] = [
    [("esc", "Esc"), ("f1", "F1"), ("f2", "F2"), ("f3", "F3"), ("f4", "F4"), ("f5", "F5"), ("f6", "F6"), ("f7", "F7"), ("f8", "F8"), ("f9", "F9"), ("f10", "F10"), ("f11", "F11"), ("f12", "F12")],
    [("`", "`"), ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"), ("6", "6"), ("7", "7"), ("8", "8"), ("9", "9"), ("0", "0"), ("-", "-"), ("=", "="), ("backspace", "Backspace")],
    [("tab", "Tab"), ("q", "Q"), ("w", "W"), ("e", "E"), ("r", "R"), ("t", "T"), ("y", "Y"), ("u", "U"), ("i", "I"), ("o", "O"), ("p", "P"), ("[", "["), ("]", "]"), ("\\", "\\")],
    [("caps_lock", "Caps"), ("a", "A"), ("s", "S"), ("d", "D"), ("f", "F"), ("g", "G"), ("h", "H"), ("j", "J"), ("k", "K"), ("l", "L"), (";", ";"), ("'", "'"), ("enter", "Enter")],
    [("shift", "Shift"), ("z", "Z"), ("x", "X"), ("c", "C"), ("v", "V"), ("b", "B"), ("n", "N"), ("m", "M"), (",", ","), (".", "."), ("/", "/"), ("shift", "Shift")],
    [("ctrl", "Ctrl"), ("cmd", "Cmd"), ("option", "Alt"), ("space", "Space"), ("option", "Alt"), ("ctrl", "Ctrl"), ("left", "←"), ("up", "↑"), ("down", "↓"), ("right", "→")],
]


def display_key_name(key: str) -> str:
    return DISPLAY_NAMES.get(key, key.upper() if len(key) == 1 else key)


def pynput_key_for(key: str):
    from pynput.keyboard import Key

    aliases = {
        "cmd": "cmd",
        "ctrl": "ctrl",
        "option": "alt",
        "left": "left",
        "right": "right",
        "up": "up",
        "down": "down",
        "page_up": "page_up",
        "page_down": "page_down",
        "caps_lock": "caps_lock",
        "delete": "delete",
    }
    attr = aliases.get(key, key)
    if attr in SPECIAL_KEY_NAMES or attr in aliases.values():
        return getattr(Key, attr)
    if len(key) == 1:
        return key
    raise ValueError(f"Unsupported key: {key}")
