from pydantic import BaseModel

from google_sheets import write_range
from roster import RaidRoster, Raider


class Shannox(BaseModel):
    roster: RaidRoster
    shannox_tank: Raider | None = None
    shannox_healer: Raider | None = None
    riplimb_tank: Raider | None = None
    riplimb_healer: Raider | None = None
    rageface_healer: Raider | None = None
    flare_cd_one: tuple[Raider] | None = None
    flare_cd_two: tuple[Raider] | None = None
    flare_cd_three: tuple[Raider] | None = None
    flare_cd_four: tuple[Raider] | None = None

    def get_assignments(self):
        pass

    def optimize(self):
        self.assign_shannox_tank()
        self.assign_shannox_healer()
        self.assign_riplimb_tank()
        self.assign_riplimb_healer()
        self.assign_rageface_healer()
        self.assign_flare_cds()

    def write(self, sheet_id: str):
        write_range(sheet_id, 'Shannox!C7:G7', [[f'=image("{self.shannox_tank.spec_link}")', self.shannox_tank.name]])
        write_range(sheet_id, 'Shannox!I7:M7', [[self.shannox_healer.name,'','','', f'=image("{self.shannox_healer.spec_link}")']])
        write_range(sheet_id, 'Shannox!C8:G8', [[f'=image("{self.riplimb_tank.spec_link}")', self.riplimb_tank.name]])
        write_range(sheet_id, 'Shannox!I8:M8', [[self.riplimb_healer.name,'','','', f'=image("{self.riplimb_healer.spec_link}")']])
        write_range(sheet_id, 'Shannox!I10:M10', [[self.rageface_healer.name,'','','', f'=image("{self.rageface_healer.spec_link}")']])

        def get_cells(assignment, ranged=False):
            if not assignment:
                if not ranged:
                    return [[f'=image("https://cdn.discordapp.com/emojis/1161060152842125372.webp?size=240&quality=lossless")','Empty']]
                else:
                    return [['Empty','','','', f'=image("https://cdn.discordapp.com/emojis/1161060152842125372.webp?size=240&quality=lossless")']]
            if ranged and len(assignment) > 1:
                return [[assignment[1].name,'','','', f'=image("{assignment[1].spec_link}")']]
            elif ranged:
                return [[assignment[0].name,'','','', f'=image("{assignment[0].spec_link}")']]
            else:
                return [[f'=image("{assignment[0].spec_link}")', assignment[0].name]]

        write_range(sheet_id, 'Shannox!C16:G16', get_cells(self.flare_cd_one))
        write_range(sheet_id, 'Shannox!I16:M16', get_cells(self.flare_cd_one, ranged=True))
        write_range(sheet_id, 'Shannox!C17:G17', get_cells(self.flare_cd_two))
        write_range(sheet_id, 'Shannox!I17:M17', get_cells(self.flare_cd_two, ranged=True))
        write_range(sheet_id, 'Shannox!C18:G18', get_cells(self.flare_cd_three))
        write_range(sheet_id, 'Shannox!I18:M18', get_cells(self.flare_cd_three, ranged=True))
        write_range(sheet_id, 'Shannox!C19:G19', get_cells(self.flare_cd_four))
        write_range(sheet_id, 'Shannox!I19:M19', get_cells(self.flare_cd_four, ranged=True))

    def assign_shannox_tank(self):
        if self.shannox_tank:
            return
        self.shannox_tank = self.roster.get_tank(main_tank=True)
        self.shannox_tank.position_set = True

    def assign_shannox_healer(self):
        if self.shannox_healer:
            return
        self.shannox_healer = self.roster.get_tank_healer()
        self.shannox_healer.position_set = True

    def assign_riplimb_tank(self):
        if self.riplimb_tank:
            return
        self.riplimb_tank = self.roster.get_tank()
        self.riplimb_tank.position_set = True

    def assign_riplimb_healer(self):
        if self.riplimb_healer:
            return
        self.riplimb_healer = self.roster.get_tank_healer()
        self.riplimb_healer.position_set = True

    def assign_rageface_healer(self):
        if self.rageface_healer:
            return
        self.rageface_healer = self.roster.get_healer(preferred=['Discipline Priest'])
        self.rageface_healer.position_set = True

    def assign_flare_cds(self):
        i = 0
        for cooldowns in self.roster.get_raid_cooldowns(can_stack=False):
            i += 1
            if i == 1:
                self.flare_cd_one = cooldowns
            elif i == 2:
                self.flare_cd_two = cooldowns
            elif i == 3:
                self.flare_cd_three = cooldowns
            elif i == 4:
                self.flare_cd_four = cooldowns
