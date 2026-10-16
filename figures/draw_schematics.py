"""Draw the collision-cover and reset-serialization constructions as vector PDFs."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

plt.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix",
                     "font.size": 11, "pdf.fonttype": 42, "ps.fonttype": 42})


def save(fig, path):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    canvas = fig.bbox
    for ax in fig.axes:
        for text in ax.texts:
            box = text.get_window_extent(renderer)
            if box.x0 < canvas.x0 or box.y0 < canvas.y0 or box.x1 > canvas.x1 or box.y1 > canvas.y1:
                raise ValueError("Label outside figure: " + text.get_text())
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, metadata={"Creator": "Matplotlib", "CreationDate": None,
                                "ModDate": None}, facecolor="white")
    plt.close(fig)


def cover(path):
    fig = plt.figure(figsize=(6.3, 1.9))
    ax = fig.add_axes((.02, .02, .96, .96))
    ax.set(xlim=(0, 10), ylim=(-1.15, 1.8), aspect="equal")
    ax.axis("off")
    ax.add_patch(Rectangle((.35, -.36), 2.05, 1.02, fill=False, lw=.9))
    positions = {"a": (.9, .15), "b": (1.85, .15),
                 "u": (4.15, .15), "v": (6.55, .15), "w": (8.95, .15)}
    ax.plot([4.15, 8.95], [.15, .15], color="black", lw=1, zorder=1)
    for name, (x, y) in positions.items():
        ax.add_patch(Circle((x, y), .25, facecolor=".87" if name == "v" else "white",
                            edgecolor="black", lw=.9, zorder=2))
        ax.text(x, y, "$" + name + "$", ha="center", va="center", fontsize=12)
    ax.text(1.375, 1.08, r"$F=\{a,b\}$", ha="center", va="center", fontsize=12)
    ax.text(1.375, -.67, r"forced by $g$", ha="center", va="center")
    ax.text(6.55, 1.08, r"$G_T$", ha="center", va="center", fontsize=12)
    ax.text(6.55, -.56, r"minimum cover: $\{v\}$", ha="center", va="center")
    ax.text(6.55, -.97, r"alternative minimal cover: $\{u,w\}$", ha="center", va="center")
    save(fig, path)


def serialization(path):
    fig = plt.figure(figsize=(6.6, 2.25))
    ax = fig.add_axes((.02, .02, .96, .96))
    ax.set(xlim=(0, 12), ylim=(-.15, 4.05))
    ax.axis("off")
    labels = ["selector\n" + r"$\ell$ input bits" + "\noutputs 0",
              "response\ninput 0: next bit\ninput 1: abort",
              "spent\nboth inputs\noutput 0"]
    for x, label in zip((1.5, 6, 10.5), labels):
        ax.add_patch(Rectangle((x-1.25, 1.0), 2.5, 1.4, facecolor="white", edgecolor="black", lw=.9))
        ax.text(x, 1.7, label, ha="center", va="center", fontsize=10.5, linespacing=1.35)
    for left, right, label in ((2.75, 4.75, "valid\nselector"), (7.25, 9.25, "last bit\nor abort")):
        ax.add_patch(FancyArrowPatch((left, 1.7), (right, 1.7), arrowstyle="-|>",
                                    mutation_scale=10, color="black", lw=.9))
        ax.text((left+right)/2, 2.56, label, ha="center", va="center", fontsize=10.5)
    ax.plot([1.5, 1.5, 10.5, 10.5], [1., .35, .35, .85], color="black", lw=.9)
    ax.add_patch(FancyArrowPatch((10.5, .75), (10.5, 1.), arrowstyle="-|>",
                                mutation_scale=10, color="black", lw=.9))
    ax.text(6, -.01, "invalid selector", ha="center", va="center", fontsize=10.5)
    ax.plot([10.5, 10.5, 1.5, 1.5], [2.4, 3.3, 3.3, 2.55], ls="--", color="black", lw=.9)
    ax.plot([6, 6], [2.4, 3.3], ls="--", color="black", lw=.9)
    ax.add_patch(FancyArrowPatch((1.5, 2.68), (1.5, 2.4), arrowstyle="-|>",
                                mutation_scale=10, color="black", lw=.9))
    ax.text(6, 3.72, "reset from any phase: return to selector", ha="center", va="center")
    save(fig, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    cover(args.outdir / "cover.pdf")
    serialization(args.outdir / "serialization.pdf")
    print("Wrote two vector schematics; label bounds checked.")


if __name__ == "__main__":
    main()
