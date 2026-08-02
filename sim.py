import numpy as np

import config


class LapSim:
    def __init__(self, track, powerunit, battery, strategy):
        self.track = track
        self.pu = powerunit
        self.battery = battery
        self.strategy = strategy
        self.corners = track.corners
        self.override_extra_used = 0.0

    def _corner_info(self, s):
        s_mod = s % self.track.length
        for length, v_corner in self.corners:
            if s_mod < length:
                return s - s_mod + length, v_corner
            s_mod -= length
        return s - s_mod + self.track.length, self.corners[0][1]

    def run_lap(self, start_v=70.0):
        s = 0.0
        v = start_v
        t = 0.0
        soc_start = self.battery.soc

        log = []
        while s < self.track.length:
            corner_pos, v_corner = self._corner_info(s)
            remaining = corner_pos - s
            ds = v * config.DT
            if ds <= 0.05:
                ds = 0.05
            dt = ds / max(v, 1.0)

            throttle = 0.0
            brake = 0.0

            if v > v_corner:
                d_brake = (v * v - v_corner * v_corner) / (2.0 * config.A_BRAKE)
                if remaining <= d_brake + self.strategy.lift_coast_dist:
                    if remaining <= d_brake:
                        brake = 1.0
                    else:
                        throttle = 0.0
                else:
                    throttle = 1.0
            else:
                throttle = 1.0

            f_drag = 0.5 * config.RHO * config.CDA * v * v
            f_roll = config.CRR * config.M_CAR * config.G
            deploy_w = 0.0
            harvest_w = 0.0

            if throttle > 0.0:
                if self.strategy.overtake:
                    derate = 1.0
                else:
                    derate = self.pu.deploy_derate(v)
                frac = self.strategy.deploy_frac
                deploy_w = self.battery.deploy(config.P_MGU * derate * frac, dt)
                extra_w = 0.0
                if self.strategy.overtake and self.override_extra_used < config.OVERRIDE_EXTRA:
                    remaining = config.OVERRIDE_EXTRA - self.override_extra_used
                    extra_w = self.battery.deploy(
                        min(config.P_MGU, remaining / max(dt, 1e-9)), dt
                    )
                    self.override_extra_used += extra_w * dt
                deploy_w += extra_w
                f_mgu = deploy_w / max(v, 1.0)
                if self.strategy.superclip and v > config.SUPERCLIP_V:
                    harvest_w = self.battery.harvest(config.SUPERCLIP_HARVEST, dt)
                    f_extra = -harvest_w / max(v, 1.0)
                else:
                    f_extra = 0.0
                f_drive = self.pu.ice_force(v) + f_mgu + f_extra
                a_net = (f_drive - f_drag - f_roll) / config.M_CAR
                a_net = min(a_net, config.A_TRACTION)
            else:
                if brake > 0.0:
                    harvest_w = self.battery.harvest(
                        min(config.P_MGU, config.A_BRAKE * config.M_CAR * v * config.MGU_EFF),
                        dt,
                    )
                    a_net = -config.A_BRAKE
                else:
                    harvest_w = self.battery.harvest(0.6 * config.P_MGU, dt)
                    f_regen = harvest_w / max(v, 1.0)
                    a_net = -((f_drag + f_roll + f_regen) / config.M_CAR)

            v_new = v + a_net * dt
            if v_new < 1.0:
                v_new = 1.0
            vmax_here = config.effective_vmax(self.battery.soc)
            if v_new > vmax_here:
                v_new = vmax_here
            if brake > 0.0 and v_new < v_corner:
                v_new = v_corner

            s += ds
            t += dt
            v = v_new
            log.append(
                (s, v, t, throttle, brake, deploy_w, harvest_w, self.battery.soc)
            )

        log = np.array(log)
        return {
            "lap_time": t,
            "soc_start": soc_start,
            "soc_end": self.battery.soc,
            "deployed_mj": self.battery.deployed_lap / 1e6,
            "harvested_mj": self.battery.harvested_lap / 1e6,
            "avg_v": self.track.length / t,
            "log": log,
        }
