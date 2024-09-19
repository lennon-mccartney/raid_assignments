from pydantic import BaseModel

from assignments.core import Assignment
from google_sheets import SHEET_ID, get_range, write_range
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
        self._cells = get_range(SHEET_ID, 'TotFW Assigns!AU19:BO33')
        for row in self._cells:
            anshal = self.roster.get_raider_by_name(row[1])
            if anshal is not None:
                self.anshal.append(anshal)
                anshal.position_set = True
            rohash = self.roster.get_raider_by_name(row[8])
            if rohash is not None:
                self.rohash.append(rohash)
                rohash.position_set = True
            nezir = self.roster.get_raider_by_name(row[15])
            if nezir is not None:
                self.nezir.append(nezir)
                nezir.position_set = True

    def optimize(self):
        tank = self.roster.get_main_tank()
        if not tank.position_set:
            self.nezir.append(tank)
            tank.position_set = True
        for tank in self.roster.get_tanks():
            if not tank.position_set:
                self.anshal.append(tank)
                tank.position_set = True

        for healer in self.roster.get_healers():
            if healer.position_set:
                continue
            if healer.wow_class in [WowClass.SHAMAN.value, WowClass.PALADIN.value] and self.nezir.healer_count() < 2:
                if self.nezir.healer_count() < 2:
                    self.nezir.append(healer)
                    healer.position_set = True
            else:
                if not self.anshal.healer_count() < 2:
                    self.anshal.append(healer)
                    healer.position_set = True
                elif not self.rohash.healer_count() < 1:
                    self.rohash.append(healer)
                    healer.position_set = True
                elif self.nezir.healer_count() < 2:
                    self.nezir.append(healer)
                    healer.position_set = True
            if not healer.position_set:
                spot = min([self.anshal, self.rohash, self.nezir], key=len)
                spot.append(healer)
                healer.position_set = True

        for raider in self.roster.get_melee():
            if raider.position_set:
                continue
            if raider.spec in ['Retribution', 'Enhancement', 'Feral'] or raider.wow_class == WowClass.ROGUE.value:
                self.rohash.append(raider)
            else:
                spot = min([self.rohash, self.anshal], key=len)
                spot.append(raider)
            raider.position_set = True
        for raider in self.roster.get_ranged():
            if raider.position_set:
                continue
            if raider.wow_class == WowClass.WARLOCK.value:
                self.rohash.append(raider)
            elif raider.wow_class == WowClass.HUNTER.value:
                self.anshal.append(raider)
            else:
                spot = min([self.rohash, self.anshal], key=len)
                spot.append(raider)
            raider.position_set = True


    def write(self):
        if self._cells is None:
            self._cells = get_range(SHEET_ID, 'TotFW Assigns!AU19:BO33')
        for i, raider in enumerate(self.anshal):
            try:
                if raider:
                    self._cells[i][1] = raider.name
                else:
                    self._cells[i][1] = 'Empty'
            except IndexError:
                print(f'{raider.name} does not have a spot ({i})')
        for i, raider in enumerate(self.rohash):
            try:
                if raider:
                    self._cells[i][8] = raider.name
                else:
                    self._cells[i][8] = 'Empty'
            except IndexError:
                print(f'{raider.name} does not have a spot ({i})')
        for i, raider in enumerate(self.nezir):
            try:
                if raider:
                    self._cells[i][15] = raider.name
                else:
                    self._cells[i][15] = 'Empty'
            except IndexError:
                print(f'{raider.name} does not have a spot ({i})')
        write_range(SHEET_ID, 'TotFW Assigns!AU19:BO33', self._cells)