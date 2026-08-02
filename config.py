RHO = 1.225
G = 9.81
CRR = 0.012
CDA = 0.75

M_CAR = 850.0

P_ICE = 400.0e3
P_MGU = 350.0e3

A_TRACTION = 35.0
A_BRAKE = 40.0
A_LAT = 30.0
MGU_EFF = 0.90

SOC_WINDOW = 4.0e6
HARVEST_CAP_LAP = 8.5e6
SOC_START = 3.2e6

DERATE_BEGIN = 290.0 / 3.6
DERATE_END = 355.0 / 3.6

V_MAX = 355.0 / 3.6
V_MIN = 20.0 / 3.6

# Manual Override lets the PU keep deploying right up to the full top speed,
# so the chaser can genuinely out-pace a derated/low-battery leader on a
# straight (that is the whole point of the 2026 overtake rule).
OVERRIDE_LIMIT = V_MAX
OVERRIDE_EXTRA = 0.5e6

SUPERCLIP_V = 250.0 / 3.6
SUPERCLIP_HARVEST = 120.0e3

# Top speed achievable with a depleted battery (ICE-only, no MGU assist).
V_MAX_EMPTY = 341.0 / 3.6


def effective_vmax(soc):
    """Interpolate top speed between empty and full battery."""
    frac = max(0.0, min(1.0, soc / SOC_WINDOW))
    return V_MAX_EMPTY + (V_MAX - V_MAX_EMPTY) * frac

DT = 0.01