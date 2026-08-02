"""Shared dark 'telemetry' matplotlib theme for all project figures."""

BG = "#0d1117"          # near-black background (GitHub dark)
PANEL = "#161b22"       # slightly lighter plot panel
GRID = "#2d333b"        # subtle grid lines
INK = "#e6edf3"         # primary text / lines
MUTED = "#8b949e"       # secondary text
AXIS = "#30363d"        # axis spines

# Accent palette (F1-telemetry inspired)
BLUE = "#1f6feb"        # leader / primary
RED = "#e10600"         # chaser / alerts  (Ferrari red)
ORANGE = "#f5a623"      # override flash
CYAN = "#39c5cf"
GREEN = "#3fb950"
PURPLE = "#bc8cff"
YELLOW = "#d29922"
GRAY = "#6e7681"

SCEN = {
    "Qualifying": RED,
    "Race (balanced)": BLUE,
    "Attack (deploy)": ORANGE,
    "Overtake": PURPLE,
    "Conserve (bank)": GREEN,
}


def apply(fig=None):
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    mpl.rcParams.update(
        {
            "figure.facecolor": PANEL,
            "axes.facecolor": PANEL,
            "savefig.facecolor": PANEL,
            "text.color": INK,
            "axes.edgecolor": AXIS,
            "axes.labelcolor": INK,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "grid.color": GRID,
            "legend.facecolor": PANEL,
            "legend.edgecolor": AXIS,
            "figure.dpi": 100,
        }
    )
    plt.rc("axes", titlecolor=INK)
    plt.rc("axes", labelcolor=INK)