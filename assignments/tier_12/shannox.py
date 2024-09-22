from pydantic import BaseModel

from roster import RaidRoster, Raider


class Shannox(BaseModel):
    roster: RaidRoster
    shannox_tank: Raider | None = None
    shannox_healer: Raider | None = None
    riplimb_tank: Raider | None = None
    riplimb_healer: Raider | None = None
    rageface_healer: Raider | None = None

    def get_assignments(self):
        pass

    def optimize(self):
        self.assign_shannox_tank()
        self.assign_shannox_healer()
        self.assign_rageface_healer()
        self.assign_riplimb_tank()
        self.assign_riplimb_healer()

    def write(self):
        pass

    def assign_shannox_tank(self):
        if self.shannox_tank:
            return
        self.shannox_tank = self.roster.get_tank(main_tank=True)

    def assign_shannox_healer(self):
        if self.shannox_healer:
            return
        self.shannox_healer = self.roster.get_tank_healer()

    def assign_riplimb_tank(self):
        if self.riplimb_tank:
            return
        self.riplimb_tank = self.roster.get_tank()

    def assign_riplimb_healer(self):
        if self.riplimb_healer:
            return
        self.riplimb_tank = self.roster.get_tank_healer()

    def assign_rageface_healer(self):
        if self.rageface_healer:
            return
        self.rageface_healer = self.roster.get_healer(preferred=['Discipline Priest'])
