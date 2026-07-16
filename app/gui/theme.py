"""
Shared color palette for the app. Ensures consistent theming (and correct
light/dark text contrast) across every GUI module instead of each widget
picking its own colors ad hoc.

CustomTkinter color values are (light_mode, dark_mode) tuples.
"""
ACCENT = ("#5B5FEF", "#4A4FD6")
ACCENT_HOVER = ("#4448D2", "#3A3EC2")

SUCCESS = ("#2FAE60", "#249150")

SURFACE = ("gray95", "gray14")
BORDER = ("gray70", "gray35")

TEXT_PRIMARY = ("gray10", "gray90")
TEXT_MUTED = ("gray45", "gray60")

SIDEBAR_HOVER = ("#E8E9FD", "#2A2B4A")

PROGRESS_TRACK = ("gray80", "gray25")