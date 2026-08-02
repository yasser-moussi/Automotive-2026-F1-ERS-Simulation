from dataclasses import dataclass


@dataclass
class Strategy:
    name: str
    deploy_frac: float = 1.0
    lift_coast_dist: float = 0.0
    superclip: bool = False
    overtake: bool = False
    desc: str = ""


def quali():
    return Strategy(
        "Qualifying",
        deploy_frac=1.0,
        superclip=True,
        desc="Maximum deploy every straight; superclips derated high-speed energy "
             "back into the battery to recover after the initial dump."
    )


def race_balanced():
    return Strategy(
        "Race (balanced)",
        deploy_frac=0.55,
        lift_coast_dist=80.0,
        superclip=True,
        desc="Deploy/harvest balanced so SoC stays roughly flat each lap."
    )


def lift_coast_heavy():
    return Strategy(
        "Race (lift-and-coast)",
        deploy_frac=0.35,
        lift_coast_dist=220.0,
        superclip=True,
        desc="Aggressive early lift to charge battery; slower laps but banked energy."
    )


def overtake():
    return Strategy(
        "Overtake",
        deploy_frac=1.0,
        overtake=True,
        desc="Following car within 1s: full 350kW up to 355km/h + 0.5MJ extra."
    )


def post_overtake_recharge():
    return Strategy(
        "Recharge (post-overtake)",
        deploy_frac=0.5,
        lift_coast_dist=120.0,
        superclip=True,
        desc="After taking the lead the car eases off, lifts-and-coasts and "
             "superclips to restore battery that the overtake burned."
    )


def conserve():
    return Strategy(
        "Conserve (bank)",
        deploy_frac=0.15,
        lift_coast_dist=260.0,
        superclip=True,
        desc="Lap 1 of bank-and-attack: minimal deploy, heavy charge. Battery fills."
    )


def attack():
    return Strategy(
        "Attack (deploy)",
        deploy_frac=1.0,
        superclip=True,
        desc="Burn the banked charge for a fast lap, then superclip-recover the "
             "battery after the dump."
    )
