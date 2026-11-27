"""Re-render the cohort retention heatmap in the report deck's berry palette."""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from explore import cohort_retention, load_clean  # noqa: E402

INK, MUTED = "#33202C", "#716572"

ret = cohort_retention(load_clean())
data = ret.values
fig, ax = plt.subplots(figsize=(8.6, 4.9))
im = ax.imshow(data, cmap="RdPu", vmin=0, vmax=50, aspect="auto")
ax.set_yticks(range(len(ret.index)),
              [p.strftime("%b %y") for p in ret.index], fontsize=8, color=MUTED)
ax.set_xticks(range(data.shape[1]), range(data.shape[1]), fontsize=8, color=MUTED)
ax.set_xlabel("Months since first purchase", color=MUTED, fontsize=9)
n_cohorts, n_offsets = data.shape
for i in range(n_cohorts):
    max_offset = n_offsets - 1 - i
    for j in range(min(n_offsets, max_offset + 1)):
        val = data[i, j]
        color = "white" if val > 32 else INK
        ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                fontsize=7, color=color)
for spine in ax.spines.values():
    spine.set_visible(False)
(HERE / "assets").mkdir(exist_ok=True)
fig.tight_layout(pad=0.4)
fig.savefig(HERE / "assets" / "cohort_retention_berry.png", dpi=160,
            transparent=True)
print("saved assets/cohort_retention_berry.png")
