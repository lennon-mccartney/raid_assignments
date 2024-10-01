from __future__ import annotations

import logging
from enum import Enum
from typing import Generator, Iterator

import requests
from PIL import ImageColor
from pydantic import BaseModel, computed_field

from google_sheets import SHEET_ID, format_cells

LOGGER = logging.getLogger(__name__)


class RaiderUnavailable(BaseException):
    pass


class Role(Enum):
    TANKS = 'tanks'
    MELEE = 'melee'
    HEALERS = 'healers'
    RANGED = 'ranged'


class WowClass(Enum):
    MAGE = 'mage'
    HUNTER = 'hunter'
    DEATH_KNIGHT = 'death knight'
    DRUID = 'druid'
    PALADIN = 'paladin'
    PRIEST = 'priest'
    ROGUE = 'rogue'
    SHAMAN = 'shaman'
    WARLOCK = 'warlock'
    WARRIOR = 'warrior'


class RaidRoster(BaseModel):
    raiders: list[Raider]

    def __iter__(self) -> Iterator[Raider]:
        return self.raiders.__iter__()

    def model_post_init(self, __context):
        print('do you have flex healers? (y/n)')
        user_input = input()
        if user_input == 'y':
            potential_healers = [x for x in self.get_potential_flex_healers()]
            print('which raiders are flex healers? (csv, ex. 1,3,5). Order by who will flex first.')
            for i, healer in enumerate(potential_healers):
                print(i, healer.name)
            user_input = input()
            for i, idx in enumerate(user_input.split(',')):
                raider: Raider = potential_healers[int(idx)]
                raider.flex_healer = i
                print(f'what is {raider.name}\'s flex spec?')
                raider.flex_spec = input()
        self.set_main_tank()

    @classmethod
    def from_raid_plan(cls, raid_id: int) -> RaidRoster:
        response = requests.get(f'https://raid-helper.dev/api/raidplan/{raid_id}')
        if response.status_code != 200:
            raise Exception(response.content)
        return cls(raiders=[Raider.from_raid_plan_data(x) for x in response.json()['raidDrop'] if x['name'] is not None])

    def add_raider(self, raider: Raider) -> None:
        self.raiders.append(raider)

    def get_healers(self, flex: int = 0) -> Generator[Raider]:
        for raider in self.raiders:
            if raider.role == Role.HEALERS:
                yield raider
            elif raider.flex_healer is not None and raider.flex_healer < flex:
                yield raider

    def get_healer(self, preferred: list[str] | None = None, last: list[str] | None = None, flex: int = 0, available: bool = True) -> Raider:
        if preferred:
            for raider in self.get_healers(flex=flex):
                if raider.class_and_spec in preferred:
                    if available and raider.position_set:
                        continue
                    return raider
        if last:
            for raider in self.get_healers(flex=flex):
                if raider.class_and_spec not in last:
                    if available and raider.position_set:
                        continue
                    return raider
        for raider in self.get_healers(flex=flex):
            if available and raider.position_set:
                continue
            return raider
        raise RaiderUnavailable()

    def get_tank_healer(self):
        return self.get_healer(preferred=['restoration shaman', 'holy paladin'], last=['restoration druid', 'discipline priest'])

    def get_raider_by_name(self, name: str) -> Raider:
        return next((x for x in self.raiders if x.name == name), None)

    def get_tanks(self, flex: int = 0) -> Generator[Raider]:
        for raider in self.raiders:
            if raider.role == Role.TANKS:
                yield raider

    def set_main_tank(self):
        for raider in self.get_tanks():
            raider.main_tank = False
        raider = self.get_tank(preferred=['blood death knight'], last=['guardian druid'], available=False)
        raider.main_tank = True

    def get_tank(self, preferred: list[str] | None = None, last: list[str] | None = None, flex: int = 0, available: bool = True, main_tank: bool = False) -> Raider:
        if main_tank:
            for raider in self.get_tanks(flex=flex):
                if raider.main_tank:
                    return raider
            self.set_main_tank()
            return self.get_tank(main_tank=True)
        if preferred:
            for raider in self.get_tanks(flex=flex):
                if raider.class_and_spec in preferred:
                    if raider.main_tank or available and raider.position_set:
                        continue
                    return raider
        if last:
            for raider in self.get_tanks(flex=flex):
                if raider.class_and_spec not in last:
                    if raider.main_tank or available and raider.position_set:
                        continue
                    return raider
        for raider in self.get_tanks(flex=flex):
            if raider.main_tank or available and raider.position_set:
                continue
            return raider
        raise RaiderUnavailable()

    def get_raider(self, role: Role = None, preferred: list[str] = None, last: list[str] = None, available: bool = True, strict: bool = False ) -> Raider:
        if preferred:
            for raider in self.raiders:
                if role and raider.role != role:
                    continue
                if preferred and raider.class_and_spec in preferred:
                    if available and raider.position_set:
                        continue
                    return raider
            if strict:
                raise RaiderUnavailable()
        if last:
            for raider in self.raiders:
                if role and raider.role != role:
                    continue
                if raider.class_and_spec not in last:
                    if available and raider.position_set:
                        continue
                    return raider
        for raider in self.raiders:
            if role and raider.role != role:
                continue
            if available and raider.position_set:
                continue
            return raider

    def get_raiders(self, role: Role = None, preferred: list[str] = None, last: list[str] = None, available: bool = True, strict: bool = False ) -> Generator[Raider]:
        if preferred:
            for raider in self.raiders:
                if role and raider.role != role:
                    continue
                if preferred and raider.class_and_spec in preferred:
                    if available and raider.position_set:
                        continue
                    yield raider
        if not strict:
            if last:
                for raider in self.raiders:
                    if role and raider.role != role:
                        continue
                    if raider.class_and_spec not in last:
                        if available and raider.position_set:
                            continue
                        yield raider
            for raider in self.raiders:
                if role and raider.role != role:
                    continue
                if available and raider.position_set:
                    continue
                yield raider

    def get_enhancement_shamans(self) -> Generator[Raider]:
        for raider in self.raiders:
            if raider.spec == 'enhancement':
                yield raider

    def get_elemental_shamans(self) -> Generator[Raider]:
        for raider in self.raiders:
            if raider.spec == 'elemental':
                yield raider

    def get_death_knights(self) -> Generator[Raider]:
        for raider in self.raiders:
            if raider.wow_class == WowClass.DEATH_KNIGHT.value:
                yield raider

    def get_death_knight(self, role: Role = None, preferred: list[str] = None) -> Raider:
        for raider in self.get_death_knights():
            if raider.role == role:
                return raider
        raise RaiderUnavailable()

    def get_rogues(self) -> Generator[Raider]:
        for raider in self.raiders:
            if raider.wow_class == WowClass.ROGUE.value:
                yield raider

    def get_warlocks(self) -> Generator[Raider]:
        for raider in self.raiders:
            if raider.wow_class == WowClass.WARLOCK.value:
                yield raider

    def get_melee(self) -> Generator[Raider]:
        for raider in self.raiders:
            if raider.role == Role.MELEE:
                yield raider

    def get_ranged(self) -> Generator[Raider]:
        for raider in self.raiders:
            if raider.role == Role.RANGED:
                yield raider

    def get_potential_flex_healers(self):
        for raider in self.get_melee():
            if raider.wow_class in [WowClass.PALADIN.value, WowClass.SHAMAN.value, WowClass.DRUID.value]:
                yield raider
        for raider in self.get_ranged():
            if raider.wow_class in [WowClass.SHAMAN.value, WowClass.PRIEST.value, WowClass.DRUID.value]:
                yield raider

    def get_raid_cooldowns(self, can_stack: bool = True, burst: bool = True) -> Generator[tuple[Raider]]:
        if can_stack:
            preferred = ['restoration shaman', 'discipline priest']
            if burst:
                preferred.append('unholy death knight')
            for raider in self.get_raiders(preferred=preferred, strict=True, available=False):
                yield raider,
        else:
            cds = list(self.get_raiders(preferred=['restoration shaman', 'discipline priest'], strict=True, available=False))
            if burst:
                dk_cds = list(self.get_raiders(preferred=['unholy death knight'], strict=True, available=False))
                for raider1, raider2 in zip(dk_cds, cds):
                    yield raider1, raider2
                if len(cds) > len(dk_cds):
                    cds = cds[len(dk_cds):]
                else:
                    cds = []
            icds = iter(cds)
            try:
                for cd1, cd2 in zip(icds):
                    yield cd1, cd2
            except ValueError:
                pass
        for raider1, raider2 in zip(self.get_raiders(preferred=['holy paladin'], strict=True), self.get_raiders(preferred=['arms warrior', 'fury warrior', 'protection warrior'], strict=True, available=False)):
            yield raider1, raider2

    def conditional_format(self, sheet_id: str, gids: list[str]) -> None:
        data = {'requests': []}
        for i, raider in enumerate(self.raiders):
            red, green, blue = (x/255 for x in ImageColor.getrgb(raider.color))
            data['requests'].extend([
                {
                    'addConditionalFormatRule': {
                        'rule': {
                            'ranges': [
                                {
                                    'sheetId': x,
                                    'startRowIndex': 0,
                                    'endRowIndex': 300,
                                    'startColumnIndex': 0,
                                    'endColumnIndex': 200,
                                }
                            ],
                            'booleanRule': {
                                'condition': {
                                    'type': 'TEXT_EQ',
                                    'values': [{'userEnteredValue': raider.name}]
                                },
                                'format': {
                                    'backgroundColor': {
                                        'green': green,
                                        'red': red,
                                        'blue': blue,
                                    }
                                }
                            }
                        },
                        'index': i,
                    }
                }
            ] for x in gids)
            # ] for x in ['1211611579', '278294734', '44485663'])
        format_cells(sheet_id, data)


class Raider(BaseModel):
    party: int
    slot: int
    name: str
    discord_id: int | str | None
    wow_class: str
    spec: str
    spec_emote: str
    role: Role
    color: str
    position_set: bool = False
    flex_healer: int | None = None
    flex_spec: str | None = None
    main_tank: bool = False

    @computed_field
    def class_and_spec(self) -> str:
        return f'{self.spec} {self.wow_class}'

    @classmethod
    def from_raid_plan_data(cls, data: dict) -> Raider:
        role, wow_class, spec = get_spec_info(data['spec'])
        print()
        return cls(
            party=data['partyId'],
            slot=data['slotId'],
            name=data['name'],
            discord_id=data.get('userid'),
            wow_class=wow_class,
            spec=spec,
            role=role,
            color=data['color'],
            spec_emote=data['spec_emote'],
        )

    @computed_field()
    def spec_link(self) -> str:
        return f'https://cdn.discordapp.com/emojis/{self.spec_emote}.png'

def get_raid_plan(raid_number: int) -> list[Raider]:
    response = requests.get(f'https://raid-helper.dev/api/raidplan/{raid_number}')
    return [Raider.from_raid_plan(x) for x in response.json()['raidDrop'] if x['name'] is not None]


def get_spec_info(spec: str) -> (Role, WowClass, str):
    match spec:
        case 'Protection':
            role = Role.TANKS
            wow_class = WowClass.WARRIOR
            spec = 'protection'
        case 'Protection1':
            role = Role.TANKS
            wow_class = WowClass.PALADIN
            spec = 'protection'
        case 'Guardian':
            role = Role.TANKS
            wow_class = WowClass.DRUID
            spec = 'guardian'
        case 'Blood_Tank':
            role = Role.TANKS
            wow_class = WowClass.DEATH_KNIGHT
            spec = 'blood'
        case 'Frost_Tank':
            role = Role.TANKS
            wow_class = WowClass.DEATH_KNIGHT
            spec = 'frost'
        case 'Unholy_Tank':
            role = Role.TANKS
            wow_class = WowClass.DEATH_KNIGHT
            spec = 'unholy'
        case 'Blood_DPS':
            role = Role.MELEE
            wow_class = WowClass.DEATH_KNIGHT
            spec = 'blood'
        case 'Frost_DPS':
            role = Role.MELEE
            wow_class = WowClass.DEATH_KNIGHT
            spec = 'frost'
        case 'Unholy_DPS':
            role = Role.MELEE
            wow_class = WowClass.DEATH_KNIGHT
            spec = 'unholy'
        case 'Arms':
            role = Role.MELEE
            wow_class = WowClass.WARRIOR
            spec = 'arms'
        case 'Fury':
            role = Role.MELEE
            wow_class = WowClass.WARRIOR
            spec = 'fury'
        case 'Balance':
            role = Role.RANGED
            wow_class = WowClass.DRUID
            spec = 'balance'
        case 'Feral':
            role = Role.MELEE
            wow_class = WowClass.DRUID
            spec = 'feral'
        case 'Restoration':
            role = Role.HEALERS
            wow_class = WowClass.DRUID
            spec = 'restoration'
        case 'Holy1':
            role = Role.HEALERS
            wow_class = WowClass.PALADIN
            spec = 'restoration'
        case 'Retribution':
            role = Role.MELEE
            wow_class = WowClass.PALADIN
            spec = 'retribution'
        case 'Assassination':
            role = Role.MELEE
            wow_class = WowClass.ROGUE
            spec = 'assassination'
        case 'Combat':
            role = Role.MELEE
            wow_class = WowClass.ROGUE
            spec = 'combat'
        case 'Subtlety':
            role = Role.MELEE
            wow_class = WowClass.ROGUE
            spec = 'subtlety'
        case 'Beastmastery':
            role = Role.RANGED
            wow_class = WowClass.HUNTER
            spec = 'beast mastery'
        case 'Marksmanship':
            role = Role.RANGED
            wow_class = WowClass.HUNTER
            spec = 'marksmanship'
        case 'Survival':
            role = Role.RANGED
            wow_class = WowClass.HUNTER
            spec = 'survival'
        case 'Frost':
            role = Role.RANGED
            wow_class = WowClass.MAGE
            spec = 'frost'
        case 'Fire':
            role = Role.RANGED
            wow_class = WowClass.MAGE
            spec = 'fire'
        case 'Arcane':
            role = Role.RANGED
            wow_class = WowClass.MAGE
            spec = 'arcane'
        case 'Affliction':
            role = Role.RANGED
            wow_class = WowClass.WARLOCK
            spec = 'affliction'
        case 'Demonology':
            role = Role.RANGED
            wow_class = WowClass.WARLOCK
            spec = 'demonology'
        case 'Destruction':
            role = Role.RANGED
            wow_class = WowClass.WARLOCK
            spec = 'destruction'
        case 'Discipline':
            role = Role.HEALERS
            wow_class = WowClass.PRIEST
            spec = 'discipline'
        case 'Holy':
            role = Role.HEALERS
            wow_class = WowClass.PRIEST
            spec = 'holy'
        case 'Shadow':
            role = Role.RANGED
            wow_class = WowClass.PRIEST
            spec = 'shadow'
        case 'Elemental':
            role = Role.RANGED
            wow_class = WowClass.SHAMAN
            spec = 'elemental'
        case 'Restoration1':
            role = Role.HEALERS
            wow_class = WowClass.SHAMAN
            spec = 'restoration'
        case 'Enhancement':
            role = Role.MELEE
            wow_class = WowClass.SHAMAN
            spec = 'enhancement'
        case _:
            LOGGER.warning(f'we did not find info for this role {spec}')
            role = Role.TANKS
            wow_class = WowClass.PRIEST
            spec = 'unknown'
    return role, wow_class, spec
