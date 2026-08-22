"""One matplotlib style for every exhibit in this project. No ad-hoc styling
in notebooks — every chart imports from here."""
import matplotlib.pyplot as plt

PALETTE = {
    "long": "#1f6f4a",
    "put": "#b23b3b",
    "call": "#c98a2c",
    "neutral": "#3b5a8a",
    "grid": "#d9d9d9",
    "text": "#222222",
}

FIGSIZE = (10, 6)
DPI = 300


def apply_style():
    """Apply the project-wide matplotlib rcParams. Call once at the top of
    every notebook, before any figure is created."""
    plt.rcParams.update({
        "figure.figsize": FIGSIZE,
        "figure.dpi": 110,
        "savefig.dpi": DPI,
        "font.size": 11,
        "axes.edgecolor": "#888888",
        "axes.grid": True,
        "grid.color": PALETTE["grid"],
        "grid.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.family": "sans-serif",
    })


def source_note(ax, text: str):
    """Stamp a small source/date citation below the x-axis. Every exhibit in
    this project carries one — no chart ships without a stated source."""
    ax.annotate(text, xy=(0, -0.14), xycoords="axes fraction",
                fontsize=8, color="#666666", ha="left")
