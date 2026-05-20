"""
Collatz Vector Sequence Visualizer
===================================
Visualizes the growing-vector Collatz recurrence:

    v_{n+1} = (floor(x_0/2), ..., floor(x_n/2), C(sum of floors))

where C(k) = k/2 if k even, 3k+1 if k odd.

Requirements:
    pip install matplotlib

Run:
    python collatz_visualizer.py
"""

import math
import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker as ticker


# ── Collatz logic ──────────────────────────────────────────────────────────────

def collatz(k: int) -> int:
    return k // 2 if k % 2 == 0 else 3 * k + 1


def build_sequence(s: int, max_steps: int = 100) -> list:
    """Return list of dicts {vec, Hn} for steps 0..max_steps."""
    steps = [{"vec": [s], "Hn": None}]
    vec = [s]
    for _ in range(max_steps):
        halved = [x // 2 for x in vec]
        Hn = sum(halved)
        new_vec = halved + [collatz(Hn)]
        steps.append({"vec": new_vec, "Hn": Hn})
        vec = new_vec
        if all(v == 0 for v in vec):
            break
    return steps


# ── App ────────────────────────────────────────────────────────────────────────

class CollatzApp:
    MAX_STEPS = 100
    PLAY_INTERVAL_MS = 1200          # ms per animation frame

    DOT_COLOR  = "#378ADD"
    NEW_COLOR  = "#E24B4A"           # newest-element ring
    TRAIL_BASE = (55 / 255, 138 / 255, 221 / 255)  # RGB for trail dots

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Collatz Vector Visualizer")
        self.root.resizable(True, True)

        self.sequence = []
        self.current_n = 0
        self.playing = False
        self._after_id = None

        self._build_ui()
        self._recompute()

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        ctrl = ttk.Frame(self.root, padding=8)
        ctrl.pack(fill=tk.X)

        ttk.Label(ctrl, text="Start value:").grid(row=0, column=0, sticky=tk.W)
        self.s_var = tk.IntVar(value=7)
        self.s_slider = ttk.Scale(ctrl, from_=1, to=99, orient=tk.HORIZONTAL,
                                  variable=self.s_var, length=200,
                                  command=self._on_s_slider)
        self.s_slider.grid(row=0, column=1, padx=6)
        self.s_label = ttk.Label(ctrl, text="7", width=4)
        self.s_label.grid(row=0, column=2)

        self.s_entry = ttk.Entry(ctrl, width=8)
        self.s_entry.insert(0, "7")
        self.s_entry.grid(row=0, column=3, padx=6)
        self.s_entry.bind("<Return>", self._on_s_entry)

        ttk.Label(ctrl, text="  Step n:").grid(row=0, column=4, sticky=tk.W)
        self.n_var = tk.IntVar(value=0)
        self.n_slider = ttk.Scale(ctrl, from_=0, to=self.MAX_STEPS,
                                  orient=tk.HORIZONTAL, variable=self.n_var,
                                  length=200, command=self._on_n_slider)
        self.n_slider.grid(row=0, column=5, padx=6)
        self.n_label = ttk.Label(ctrl, text="0", width=4)
        self.n_label.grid(row=0, column=6)

        self.play_btn = ttk.Button(ctrl, text="▶ Play", command=self._toggle_play)
        self.play_btn.grid(row=0, column=7, padx=4)
        self.reset_btn = ttk.Button(ctrl, text="↺ Reset", command=self._reset)
        self.reset_btn.grid(row=0, column=8, padx=4)

        self.fig, self.ax = plt.subplots(figsize=(9, 4.5))
        self.fig.tight_layout(pad=2.0)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        self.status_var = tk.StringVar(value="")
        ttk.Label(self.root, textvariable=self.status_var,
                  font=("Courier", 10), anchor=tk.W,
                  padding=(8, 2)).pack(fill=tk.X)

        self.vec_var = tk.StringVar(value="")
        ttk.Label(self.root, textvariable=self.vec_var,
                  font=("Courier", 9), anchor=tk.W,
                  padding=(8, 0, 8, 4)).pack(fill=tk.X)

    # ── sequence computation ───────────────────────────────────────────────────

    def _recompute(self):
        try:
            s = max(1, int(self.s_entry.get()))
        except ValueError:
            s = 7
        self.sequence = build_sequence(s, self.MAX_STEPS)
        max_n = len(self.sequence) - 1
        self.n_slider.configure(to=max_n)
        self.current_n = min(self.current_n, max_n)
        self.n_var.set(self.current_n)
        self._draw()

    # ── drawing ────────────────────────────────────────────────────────────────

    def _max_val_up_to(self, n: int) -> float:
        m = 1
        for s in range(n + 1):
            for v in self.sequence[s]["vec"]:
                if v > m:
                    m = v
        return m

    @staticmethod
    def _log_ceil(val: float) -> float:
        if val <= 1:
            return 10
        exp = math.ceil(math.log10(val))
        return 10 ** exp

    @staticmethod
    def _fmt(v: float) -> str:
        if v >= 1e9:
            return f"{v/1e9:.3g}B"
        if v >= 1e6:
            return f"{v/1e6:.3g}M"
        if v >= 1e3:
            return f"{v/1e3:.3g}k"
        return str(int(v))

    def _draw(self):
        n = self.current_n
        step = self.sequence[n]
        vec = step["vec"]
        Hn = step["Hn"]

        raw_max = self._max_val_up_to(n)
        y_max = self._log_ceil(raw_max)
        y_min = 1

        max_len = max(len(s["vec"]) for s in self.sequence)

        ax = self.ax
        ax.cla()
        ax.set_yscale("log")
        ax.set_ylim(y_min, y_max)
        ax.set_xlim(-0.5, max(max_len - 1, 1) + 0.5)
        ax.set_xlabel("Vector index i")
        ax.set_ylabel("Value (log scale)")
        ax.set_title(f"Collatz Vector — step n = {n}", fontsize=12)
        ax.grid(True, which="major", linestyle="-", linewidth=0.4, alpha=0.3)
        ax.grid(True, which="minor", linestyle=":", linewidth=0.3, alpha=0.15)
        ax.yaxis.set_major_formatter(
            ticker.FuncFormatter(lambda v, _: self._fmt(v)))

        # trail dots — exponential fade by age
        for s_idx in range(n):
            age = n - s_idx
            alpha = max(0.03, 0.12 * (0.72 ** (age - 1)))
            sv = self.sequence[s_idx]["vec"]
            xs = [i for i, v in enumerate(sv) if v > 0]
            ys = [v for v in sv if v > 0]
            if xs:
                r, g, b = self.TRAIL_BASE
                ax.scatter(xs, ys, s=14, color=(r, g, b, alpha),
                           zorder=2, linewidths=0)

        # connecting line for current step
        nz_idx = [i for i, v in enumerate(vec) if v > 0]
        nz_val = [vec[i] for i in nz_idx]
        if len(nz_idx) > 1:
            ax.plot(nz_idx, nz_val, color=self.DOT_COLOR,
                    linewidth=1.2, alpha=0.45, zorder=3)

        # current step dots
        for i, v in enumerate(vec):
            if v <= 0:
                continue
            ax.scatter([i], [v], s=40, color=self.DOT_COLOR,
                       edgecolors="white", linewidths=1.2, zorder=4)

        # highlight newest dot
        if n > 0 and vec:
            last_i = len(vec) - 1
            last_v = vec[last_i]
            if last_v > 0:
                ax.scatter([last_i], [last_v], s=120,
                           facecolors="none", edgecolors=self.NEW_COLOR,
                           linewidths=2, zorder=5)

        self.canvas.draw()

        cur_max = max(vec) if vec else 0
        Hn_str = str(Hn) if Hn is not None else "—"
        self.status_var.set(
            f"n = {n}  |  vec length = {len(vec)}  |  Hₙ = {Hn_str}"
            f"  |  max = {cur_max:,}")
        display = ", ".join(map(str, vec[:20])) + (" …" if len(vec) > 20 else "")
        self.vec_var.set(f"v{n} = [{display}]")

    # ── controls ───────────────────────────────────────────────────────────────

    def _on_s_slider(self, _=None):
        v = int(self.s_var.get())
        self.s_label.configure(text=str(v))
        self.s_entry.delete(0, tk.END)
        self.s_entry.insert(0, str(v))
        self._stop_play()
        self.current_n = 0
        self._recompute()

    def _on_s_entry(self, _=None):
        try:
            v = max(1, int(self.s_entry.get()))
        except ValueError:
            return
        self.s_entry.delete(0, tk.END)
        self.s_entry.insert(0, str(v))
        self.s_var.set(min(v, 99))
        self.s_label.configure(text=str(min(v, 99)))
        self._stop_play()
        self.current_n = 0
        self._recompute()

    def _on_n_slider(self, _=None):
        self._stop_play()
        self.current_n = int(self.n_var.get())
        self.n_label.configure(text=str(self.current_n))
        self._draw()

    def _toggle_play(self):
        if self.playing:
            self._stop_play()
        else:
            if self.current_n >= len(self.sequence) - 1:
                self.current_n = 0
            self.playing = True
            self.play_btn.configure(text="⏸ Pause")
            self._step_play()

    def _step_play(self):
        if not self.playing:
            return
        self.current_n += 1
        self.n_var.set(self.current_n)
        self.n_label.configure(text=str(self.current_n))
        self._draw()
        if self.current_n >= len(self.sequence) - 1:
            self._stop_play()
        else:
            self._after_id = self.root.after(self.PLAY_INTERVAL_MS, self._step_play)

    def _stop_play(self):
        self.playing = False
        self.play_btn.configure(text="▶ Play")
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None

    def _reset(self):
        self._stop_play()
        self.current_n = 0
        self.n_var.set(0)
        self.n_label.configure(text="0")
        self._draw()


# ── entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app = CollatzApp(root)
    root.mainloop()