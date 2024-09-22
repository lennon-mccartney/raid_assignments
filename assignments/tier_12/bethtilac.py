import logging

from pydantic import BaseModel

from assignments.core import Assignment
from roster import RaidRoster, Raider, Role, RaiderUnavailable

LOGGER = logging.getLogger(__name__)


class Bethtilac(BaseModel):
    roster: RaidRoster
    bethtilac_tank: Raider = None
    bethtilac_healer: Raider = None
    drone_tank: Raider = None
    drone_healer: Raider = None
    drone_dps: Assignment = None
    bethtilac_dps: Assignment = None
    melee_group_one: Assignment = None
    melee_group_two: Assignment = None
    melee_group_three: Assignment = None

    def get_assignments(self):
        pass

    def optimize(self):
        self.assign_bethtilac_tank()
        self.assign_bethtilac_healer()
        self.assign_drone_tank()
        self.assign_drone_healer()
        self.assign_drone_dps()
        self.assign_bethtilac_dps()
        self.assign_melee_groups()

    def write(self):
        pass

    def assign_bethtilac_tank(self):
        if self.bethtilac_tank:
            return
        self.bethtilac_tank = self.roster.get_tank(main_tank=True)
        self.bethtilac_tank.position_set = True

    def assign_bethtilac_healer(self):
        if self.bethtilac_healer:
            return
        self.bethtilac_healer = self.roster.get_healer(preferred=['restoration shaman'])
        self.bethtilac_healer.position_set = True

    def assign_drone_tank(self):
        if self.drone_tank:
            return
        self.drone_tank = self.roster.get_tank()
        self.drone_tank.position_set = True

    def assign_drone_healer(self):
        if self.drone_healer:
            return
        self.drone_healer = self.roster.get_healer(preferred=['holy_paladin'])
        self.drone_healer.position_set = True

    def assign_drone_dps(self):
        if self.drone_dps:
            return
        self.drone_dps = self.roster.get_dps(preferred=['shadow priest', 'balance druid'])
        for dps in self.drone_dps:
            dps.position_set = True

    def assign_bethtilac_dps(self):
        if self.bethtilac_dps:
            return
        self.bethtilac_dps.extend(list(self.roster.get_rogues()))
        for dps in self.bethtilac_dps:
            dps.position_set = True

    def assign_melee_groups(self):
        def group_has_soaker(group: Assignment):
            return any([
                group.has_death_knight(),
                group.has_druid(spec='feral'),
                group.has_warrior(),
                group.has_paladin(spec='retribution')
            ])

        def soaker_count(group: Assignment):
            return sum([
                group.has_death_knight(),
                group.has_druid(spec='feral'),
                group.has_warrior(),
                group.has_paladin(spec='retribution')
            ])

        for melee_group in [self.melee_group_one, self.melee_group_two, self.melee_group_three]:
            if not group_has_soaker(melee_group):
                try:
                    raider = self.roster.get_raider(
                        preferred=[
                            'unholy death knight',
                            'feral druid',
                            'arms warrior',
                            'fury warrior',
                            'retribution paladin',
                        ],
                        strict=True,
                    )
                    melee_group.append(raider)
                    raider.position_set = True
                except RaiderUnavailable:
                    LOGGER.warning('No soaker available for melee group')
                    pass
        for soaker in self.roster.get_raiders(
                preferred=[
                    'unholy death knight',
                    'feral druid',
                    'arms warrior',
                    'fury warrior',
                    'retribution paladin',
                ],
                strict=True,
        ):
            sorted([self.melee_group_one, self.melee_group_two, self.melee_group_three], key=soaker_count)[0].append(soaker)
            soaker.position_set = True
        for dps in self.roster.get_raiders(role=Role.MELEE):
            if not dps.position_set:
                sorted([self.melee_group_one, self.melee_group_two, self.melee_group_three], key=len)[0].append(dps)
                dps.position_set = True
