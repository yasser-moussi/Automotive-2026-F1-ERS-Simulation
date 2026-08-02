import config


class Battery:
    def __init__(self):
        self.soc = config.SOC_START
        self.window = config.SOC_WINDOW
        self.harvested_lap = 0.0
        self.deployed_lap = 0.0

    def can_deploy(self, energy):
        return self.soc >= energy

    def deploy(self, power, dt):
        energy = power * dt
        if self.soc - energy < 0.0:
            energy = self.soc
        self.soc -= energy
        self.deployed_lap += energy
        return energy / dt if dt > 0 else 0.0

    def harvest(self, power, dt):
        if self.soc >= self.window:
            return 0.0
        if self.harvested_lap >= config.HARVEST_CAP_LAP:
            return 0.0
        energy = power * dt
        energy = min(energy, config.HARVEST_CAP_LAP - self.harvested_lap)
        energy = min(energy, self.window - self.soc)
        self.soc += energy
        self.harvested_lap += energy
        return energy / dt if dt > 0 else 0.0

    def reset_lap(self):
        self.harvested_lap = 0.0
        self.deployed_lap = 0.0
