import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import config
from track import monza
from powerunit import PowerUnit
from battery import Battery
from sim import LapSim
import strategy
import theme


# Per-scenario lap heuristics: (traffic sigma s, tyre wear s/lap).
# Traffic is harsher for aggressive/closer racing; markup-down cars get a clear
# push lap. Tyre wear drifts stints slightly slower over the 5 laps.
_VAR_SIGMA = {
    "Qualifying": (0.02, 0.008),
    "Race (balanced)": (0.05, 0.012),
    "Attack (deploy)": (0.10, 0.015),
    "conserve": (0.05, 0.012),
    "attack": (0.12, 0.018),
}


def _lap_variation(category, lap):
    """Seeded per-lap realism: tyre-wear drift + traffic scatter (+ small
    energy pulse). Reproducible because the RNG is seeded from the category
    and lap number."""
    rng = np.random.default_rng(abs(hash(f"{category}-L{lap}")) % (2**31))
    t_sigma, wear_per = _VAR_SIGMA.get(category, (0.05, 0.012))
    tyre = wear_per * (lap - 1)
    traffic = float(np.clip(rng.normal(0.0, t_sigma), -0.30, 0.40))
    t_adj = tyre + traffic
    e_adj = float(np.clip(rng.normal(0.0, 0.12), -0.30, 0.40))
    return t_adj, e_adj


def run_stint(track, strat, laps=5, soc_start=None):
    pu = PowerUnit()
    battery = Battery()
    if soc_start is not None:
        battery.soc = soc_start
    sim = LapSim(track, pu, battery, strat)

    rows = []
    for i in range(laps):
        battery.reset_lap()
        res = sim.run_lap()
        t_adj, e_adj = _lap_variation(strat.name, i + 1)
        rows.append(
            dict(
                lap=i + 1,
                time=res["lap_time"] + t_adj,
                soc_end=res["soc_end"] / 1e6,
                deployed=max(0.0, res["deployed_mj"] + e_adj * 0.5),
                harvested=max(0.0, res["harvested_mj"] + e_adj * 0.3),
                avg_v=res["avg_v"],
            )
        )
    return pd.DataFrame(rows)


def plot_strategy_one_lap(strat, track):
    pu = PowerUnit()
    battery = Battery()
    if strat.name == "Attack (deploy)":
        battery.soc = config.SOC_WINDOW
    sim = LapSim(track, pu, battery, strat)
    battery.reset_lap()
    res = sim.run_lap()
    log = res["log"]
    return log[:, 0], log[:, 1], log[:, 7] / 1e6  # s, v, soc


def run_bank_attack(track, conserve_laps=3, attack_laps=1):
    pu = PowerUnit()
    battery = Battery()
    sim_c = LapSim(track, pu, battery, strategy.conserve())
    sim_a = LapSim(track, pu, battery, strategy.attack())
    rows = []
    for i in range(conserve_laps):
        battery.reset_lap()
        res = sim_c.run_lap()
        t_adj, e_adj = _lap_variation("conserve", i + 1)
        rows.append(dict(lap=i + 1, phase="conserve", time=res["lap_time"] + t_adj,
                         soc_end=res["soc_end"] / 1e6,
                         deployed=max(0.0, res["deployed_mj"] + e_adj * 0.5),
                         harvested=max(0.0, res["harvested_mj"] + e_adj * 0.3),
                         avg_v=res["avg_v"]))
    for j in range(attack_laps):
        battery.reset_lap()
        res = sim_a.run_lap()
        t_adj, e_adj = _lap_variation("attack", conserve_laps + j + 1)
        rows.append(dict(lap=conserve_laps + j + 1, phase="attack",
                         time=res["lap_time"] + t_adj,
                         soc_end=res["soc_end"] / 1e6,
                         deployed=max(0.0, res["deployed_mj"] + e_adj * 0.5),
                         harvested=max(0.0, res["harvested_mj"] + e_adj * 0.3),
                         avg_v=res["avg_v"]))
    return pd.DataFrame(rows)


def main():
    theme.apply()
    track = monza()

    strats = [strategy.quali(), strategy.race_balanced(), strategy.attack()]

    print(f"Track length: {track.length:.0f} m")
    print()

    stint_frames = {}
    for st in strats:
        # Attack runs from a pre-banked full battery (its aggressiveness only
        # pays off if you've charged earlier), so it's distinct from Quali.
        soc_start = config.SOC_WINDOW if st.name == "Attack (deploy)" else None
        df = run_stint(track, st, laps=5, soc_start=soc_start)
        stint_frames[st.name] = df
        print(f"=== {st.name} ===")
        print(f"  {st.desc}")
        print(df.round(3).to_string(index=False))
        print()

    bank = run_bank_attack(track, conserve_laps=3, attack_laps=1)
    print("=== Bank-and-attack (3 conserve laps + 1 attack lap) ===")
    print(bank.round(3).to_string(index=False))
    print()

    comparison = pd.DataFrame(
        {
            st.name: {
                "avg_lap": stint_frames[st.name]["time"].mean(),
                "best_lap": stint_frames[st.name]["time"].min(),
                "first_lap": stint_frames[st.name]["time"].iloc[0],
                "last_soc_mj": stint_frames[st.name]["soc_end"].iloc[-1],
            }
            for st in strats
        }
    ).T.round(3)
    comparison.loc["Bank-and-attack (4 laps)"] = {
        "avg_lap": bank["time"].mean(),
        "best_lap": bank["time"].min(),
        "first_lap": bank["time"].iloc[0],
        "last_soc_mj": bank["soc_end"].iloc[-1],
    }
    print("=== 5-lap stint comparison ===")
    print(comparison)
    print()

    # --- Figure: independent 2x2 grid (no sharex!). Each panel owns its scale.
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    (ax1, ax2), (ax3, ax4) = axes

    # Panel 1: speed vs distance (one lap)
    for st in strats:
        s, v, _ = plot_strategy_one_lap(st, track)
        ax1.plot(s / 1000.0, v * 3.6, color=theme.SCEN[st.name], lw=1.6,
                 label=st.name)
    ax1.set_ylabel("Speed (km/h)")
    ax1.set_xlabel("Distance (km)")
    ax1.set_xlim(0, track.length / 1000.0)
    ax1.set_ylim(190, 345)
    ax1.set_title("Speed profile — one lap")
    ax1.legend(fontsize=9)
    ax1.grid(alpha=0.35)

    # Panel 2: battery SoC vs distance (one lap)
    for st in strats:
        s, _, soc = plot_strategy_one_lap(st, track)
        ax2.plot(s / 1000.0, soc, color=theme.SCEN[st.name], lw=1.6,
                 label=st.name)
    ax2.set_ylabel("Battery SoC (MJ)")
    ax2.set_xlabel("Distance (km)")
    ax2.set_xlim(0, track.length / 1000.0)
    ax2.set_title("Battery state of charge — one lap")
    ax2.legend(fontsize=9)
    ax2.grid(alpha=0.35)

    # Panel 3: lap-time grouped bars per lap 1..5, per scenario.
    lap_ids = [1, 2, 3, 4, 5]
    n = len(strats)
    width = 0.8 / n
    for j, st in enumerate(strats):
        x = np.arange(len(lap_ids)) + j * width
        bars = ax3.bar(x, stint_frames[st.name]["time"],
                       width=width, color=theme.SCEN[st.name], label=st.name)
        for r in bars:
            ax3.annotate(f"{r.get_height():.2f}",
                         (r.get_x() + r.get_width() / 2, r.get_height()),
                         ha="center", va="bottom", fontsize=8, color=theme.MUTED)
    ax3.set_xticks(np.arange(len(lap_ids)) + width * (n - 1) / 2)
    ax3.set_xticklabels([f"L{li}" for li in lap_ids])
    ax3.set_ylabel("Lap time (s)")
    ax3.set_ylim(48, 51)
    ax3.set_title("Lap time by strategy over a 5-lap stint")
    ax3.legend(fontsize=9)
    ax3.grid(alpha=0.35, axis="y")

    # Panel 4: energy — two grouped bars per scenario (deployed vs harvested)
    scen_names = [st.name for st in strats]
    deployed = [stint_frames[st.name]["deployed"].sum() for st in strats]
    harvested = [stint_frames[st.name]["harvested"].sum() for st in strats]
    x = np.arange(len(scen_names))
    w = 0.33
    bd = ax4.bar(x - w / 2, deployed, w, color=theme.RED, label="Deployed (MJ)")
    bh = ax4.bar(x + w / 2, harvested, w, color=theme.GREEN, label="Harvested (MJ)")
    ax4.set_xticks(x)
    ax4.set_xticklabels(scen_names)
    ax4.set_ylabel("Energy (MJ)")
    ax4.set_title("5-lap stint — total energy deployed vs harvested")
    ax4.legend(fontsize=9)
    ax4.grid(alpha=0.35, axis="y")
    for bars in (bd, bh):
        for r in bars:
            ax4.annotate(f"{r.get_height():.1f}",
                         (r.get_x() + r.get_width() / 2, r.get_height()),
                         ha="center", va="bottom", fontsize=8, color=theme.MUTED)

    fig.suptitle("2026 F1 ERS — strategy comparison over a 5-lap stint",
                 color=theme.INK, fontsize=14)
    fig.tight_layout()
    fig.savefig("/home/yasserr/work/f1_ers/strategy_comparison.png", dpi=130)
    print("Saved plot -> f1_ers/strategy_comparison.png")


if __name__ == "__main__":
    main()