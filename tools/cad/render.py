"""Quick flat-shaded renders of mesh groups: render.py out.png groups.npz [label positions]."""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection


def render(groups, out, views=(("front", 0, 1, 2), ("side", 2, 1, 0), ("top", 0, 2, 1)),
           labels=None, size=6, maxtri=60000, marks=None):
    """groups: list of (name, tris Nx3x3 in metres, rgb)."""
    fig, axs = plt.subplots(1, len(views), figsize=(size * len(views), size))
    rng = np.random.default_rng(0)
    light = np.array([0.3, 0.5, 0.8]); light /= np.linalg.norm(light)
    for ax, (title, a, b, depth) in zip(np.atleast_1d(axs), views):
        polys, cols, zs = [], [], []
        for name, tris, rgb in groups:
            t = tris
            if len(t) > maxtri:
                t = t[rng.choice(len(t), maxtri, replace=False)]
            n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
            n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
            sh = 0.35 + 0.65 * np.abs(n @ light)
            polys.append(t[:, :, [a, b]] * 1000)
            cols.append(np.clip(np.outer(sh, rgb), 0, 1))
            zs.append(t[:, :, depth].mean(1))
        P = np.concatenate(polys); C = np.concatenate(cols); Z = np.concatenate(zs)
        sign = -1 if title == "top" else 1
        o = np.argsort(sign * Z)
        ax.add_collection(PolyCollection(P[o], facecolors=C[o], edgecolors="none"))
        ax.autoscale(); ax.set_aspect("equal"); ax.grid(True, lw=0.3)
        ax.set_title(f"{title}: axes {'XYZ'[a]} (right), {'XYZ'[b]} (up) [mm]")
        if marks:
            for (lbl, p, c) in marks:
                ax.plot(p[a] * 1000, p[b] * 1000, "o", color=c, ms=5)
                ax.annotate(lbl, (p[a] * 1000, p[b] * 1000), fontsize=8, color=c)
    fig.tight_layout(); fig.savefig(out, dpi=90); plt.close(fig)
