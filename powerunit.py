import config


class PowerUnit:
    def __init__(self):
        self.p_ice_max = config.P_ICE
        self.p_mgu_max = config.P_MGU
        self.mgu_eff = config.MGU_EFF

    def ice_force(self, v):
        if v < 1.0:
            return config.A_TRACTION * config.M_CAR
        return min(self.p_ice_max / v, config.A_TRACTION * config.M_CAR)

    def deploy_derate(self, v):
        if v <= config.DERATE_BEGIN:
            return 1.0
        if v >= config.DERATE_END:
            return 0.0
        return (config.DERATE_END - v) / (config.DERATE_END - config.DERATE_BEGIN)

    def deploy_force(self, v, frac):
        derate = self.deploy_derate(v)
        p = self.p_mgu_max * derate * frac
        if v < 1.0:
            return config.A_TRACTION * config.M_CAR
        return min(p / v, config.A_TRACTION * config.M_CAR)
