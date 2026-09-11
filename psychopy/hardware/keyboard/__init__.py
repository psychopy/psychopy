import sysconfig


__all__ = [
    "KeyboardDevice",
    "KeyPress",
    "Keyboard"
]


if sysconfig.get_config_var("Py_GIL_DISABLED"):
    from .thread_keyboard import KeyboardDevice, KeyPress, Keyboard 
else:
    from .subprocess_keyboard import KeyboardDevice, KeyPress, Keyboard
