from pydantic import BaseModel

from assignments.core import Assignment
from google_sheets import SHEET_ID, get_range
from roster import RaidRoster, WowClass


class Conclave(BaseModel):
    roster: RaidRoster
    anshal: Assignment = Assignment()
    rohash: Assignment = Assignment()
    nezir: Assignment = Assignment()
    _cells: list[list[str]] | None = None

    class Config:
        arbitrary_types_allowed = True

    def get_assignments(self):
        for raider in self.roster:
            raider.position_set = False
        self._cells = get_range(SHEET_ID, 'TotFW Assigns!AU19:BO30')
        for row in self._cells:
            self.anshal.append(self.roster.get_raider_by_name(row[1]))
            self.rohash.append(self.roster.get_raider_by_name(row[8]))
            self.nezir.append(self.roster.get_raider_by_name(row[15]))

    def optimize(self):
        tank = self.roster.get_main_tank()
        if not tank.position_set:
            self.nezir.append(tank)
            tank.position_set = True
        for tanks in self.roster.get_tanks():
            if not tank.position_set:
                self.anshal.append(tank)
                tank.position_set = True

        for healer in self.roster.get_healers():
            if not healer.position_set:
                if healer.wow_class in [WowClass.SHAMAN.value, WowClass.PALADIN.value] and self.nezir.healer_count() < 2:
                    if self.nezir.healer_count() < 2:
                        self.nezir.append(healer)
                else:
                    if not self.anshal.healer_count() < 2:
                        self.anshal.append(healer)
                    elif not self.rohash.has_healer() < 2:
                        self.rohash.append(healer)
                    if self.nezir.healer_count() < 2:
                        self.nezir.append(healer)
                healer.position_set = True

            for raider in self.roster.get_raiders():
                if raider.spec in ['Retribution', 'Enhancement', 'Feral']:
                    pass


    def write(self):
        for i, raider in enumerate(self.anshal):
            self._cells[i][1] = raider.name
        for i, raider in enumerate(self.rohash):
            self._cells[i][8] = raider.name
        for i, raider in enumerate(self.nezir):
            self._cells[i][15] = raider.name
