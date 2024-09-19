from __future__ import annotations

import os
from enum import Enum
from typing import Generator, Iterator

import requests
from PIL import ImageColor
from pydantic import BaseModel

from google_sheets import SHEET_ID, format_cells


class Role(Enum):
    TANKS = 'tanks'
    MELEE = 'melee'
    HEALERS = 'healers'
    RANGED = 'ranged'


class WowClass(Enum):
    MAGE = 'mage'
    HUNTER = 'hunter'
    DEATH_KNIGHT = 'death_knight'
    DRUID = 'druid'
    PALADIN = 'paladin'
    PRIEST = 'priest'
    ROGUE = 'rogue'
    SHAMAN = 'shaman'
    WARLOCK = 'warlock'
    WARRIOR = 'warrior'


class RaidRoster(BaseModel):
    raiders: list[Raider]

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

    @classmethod
    def from_raid_plan(cls, raid_id: int) -> RaidRoster:
        response = requests.get(f'https://raid-helper.dev/api/raidplan/{raid_id}')
        if response.status_code != 200:
            raise Exception(response.content)
        print(response.json())
        return cls(raiders=[Raider.from_raid_plan_data(x) for x in response.json()['raidDrop'] if x['name'] is not None])

    def __iter__(self) -> Iterator[Raider]:
        return self.raiders.__iter__()

    def add_raider(self, raider: Raider) -> None:
        self.raiders.append(raider)

    def get_raider_by_name(self, name: str) -> Raider:
        return next((x for x in self.raiders if x.name == name), None)

    def get_tanks(self) -> list[Raider]:
        tanks = []
        for raider in self.raiders:
            if raider.role == Role.TANKS:
                tanks.append(raider)
        return tanks

    def get_main_tank(self) -> Raider:
        if getattr(self, 'main_tank', None):
            return self.main_tank
        main_tank = next((x for x in self.raiders if x.role == Role.TANKS and x.wow_class == WowClass.DEATH_KNIGHT.value), None)
        if not main_tank:
            main_tank = next((x for x in self.raiders if x.role == Role.TANKS and x.wow_class == WowClass.PALADIN.value), None)
        if not main_tank:
            main_tank = next((x for x in self.raiders if x.role == Role.TANKS and x.wow_class == WowClass.WARRIOR.value), None)
        if not main_tank:
            main_tank = next((x for x in self.raiders if x.role == Role.TANKS and x.wow_class == WowClass.DRUID.value), None)
        if not main_tank:
            raise Exception('Roster has no tanks')
        return main_tank

    def get_enhancement_shamans(self) -> Generator[Raider]:
        for raider in self.raiders:
            if raider.spec == 'Enhancement':
                yield raider

    def get_elemental_shamans(self) -> Generator[Raider]:
        for raider in self.raiders:
            if raider.spec == 'Elemental':
                yield raider

    def get_dks(self) -> Generator[Raider]:
        for raider in self.raiders:
            if raider.wow_class == WowClass.DEATH_KNIGHT.value:
                yield raider

    def get_rogues(self) -> Generator[Raider]:
        for raider in self.raiders:
            if raider.wow_class == WowClass.ROGUE.value:
                yield raider

    def get_warlocks(self) -> Generator[Raider]:
        for raider in self.raiders:
            if raider.wow_class == WowClass.WARLOCK.value:
                yield raider

    def get_healers(self, flex=0) -> Generator[Raider]:
        for raider in self.raiders:
            if raider.role == Role.HEALERS:
                yield raider
            elif raider.flex_healer is not None and raider.flex_healer < flex:
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

    def conditional_format(self):
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
            ] for x in ['1211611579', '278294734', '44485663'])
        format_cells(SHEET_ID, data)


class Raider(BaseModel):
    party: int
    slot: int
    name: str
    discord_id: int | None
    wow_class: str
    spec: str
    role: Role
    color: str
    position_set: bool = False
    flex_healer: int | None = None

    @classmethod
    def from_raid_plan_data(cls, data: dict) -> Raider:
        role, wow_class, spec = get_spec_info(data['spec'])
        print(data)
        return cls(
            party=data['partyId'],
            slot=data['slotId'],
            name=data['name'],
            discord_id=data['userid'] if data['userid'] != 'undefined' else None,
            wow_class=wow_class,
            spec=spec,
            role=role,
            color=data['color'],
        )


def get_raid_plan(raid_number: int) -> list[Raider]:
    response = requests.get(f'https://raid-helper.dev/api/raidplan/{raid_number}')
    return [Raider.from_raid_plan(x) for x in response.json()['raidDrop'] if x['name'] is not None]


def get_spec_info(spec: str) -> (Role, WowClass, str):
    match spec:
        case 'Protection':
            role = Role.TANKS
            wow_class = WowClass.WARRIOR
            spec = 'Protection'
        case 'Protection1':
            role = Role.TANKS
            wow_class = WowClass.PALADIN
            spec = 'Protection'
        case 'Guardian':
            role = Role.TANKS
            wow_class = WowClass.DRUID
            spec = 'Guardian'
        case 'Blood_Tank':
            role = Role.TANKS
            wow_class = WowClass.DEATH_KNIGHT
            spec = 'Blood'
        case 'Frost_Tank':
            role = Role.TANKS
            wow_class = WowClass.DEATH_KNIGHT
            spec = 'Frost'
        case 'Unholy_Tank':
            role = Role.TANKS
            wow_class = WowClass.DEATH_KNIGHT
            spec = 'Unholy'
        case 'Blood_DPS':
            role = Role.MELEE
            wow_class = WowClass.DEATH_KNIGHT
            spec = 'Blood'
        case 'Frost_DPS':
            role = Role.MELEE
            wow_class = WowClass.DEATH_KNIGHT
            spec = 'Frost'
        case 'Unholy_DPS':
            role = Role.MELEE
            wow_class = WowClass.DEATH_KNIGHT
            spec = 'Unholy'
        case 'Arms':
            role = Role.MELEE
            wow_class = WowClass.WARRIOR
            spec = 'Arms'
        case 'Fury':
            role = Role.MELEE
            wow_class = WowClass.WARRIOR
            spec = 'Fury'
        case 'Balance':
            role = Role.RANGED
            wow_class = WowClass.DRUID
            spec = 'Balance'
        case 'Feral':
            role = Role.MELEE
            wow_class = WowClass.DRUID
            spec = 'Feral'
        case 'Restoration':
            role = Role.HEALERS
            wow_class = WowClass.DRUID
            spec = 'Restoration'
        case 'Holy1':
            role = Role.HEALERS
            wow_class = WowClass.PALADIN
            spec = 'Restoration'
        case 'Retribution':
            role = Role.MELEE
            wow_class = WowClass.PALADIN
            spec = 'Retribution'
        case 'Assassination':
            role = Role.MELEE
            wow_class = WowClass.ROGUE
            spec = 'Assassination'
        case 'Combat':
            role = Role.MELEE
            wow_class = WowClass.ROGUE
            spec = 'Combat'
        case 'Subtlety':
            role = Role.MELEE
            wow_class = WowClass.ROGUE
            spec = 'Subtlety'
        case 'Beastmastery':
            role = Role.RANGED
            wow_class = WowClass.HUNTER
            spec = 'Beast Mastery'
        case 'Marksmanship':
            role = Role.RANGED
            wow_class = WowClass.HUNTER
            spec = 'Marksmanship'
        case 'Survival':
            role = Role.RANGED
            wow_class = WowClass.HUNTER
            spec = 'Survival'
        case 'Frost':
            role = Role.RANGED
            wow_class = WowClass.MAGE
            spec = 'Frost'
        case 'Fire':
            role = Role.RANGED
            wow_class = WowClass.MAGE
            spec = 'Fire'
        case 'Arcane':
            role = Role.RANGED
            wow_class = WowClass.MAGE
            spec = 'Arcane'
        case 'Affliction':
            role = Role.RANGED
            wow_class = WowClass.WARLOCK
            spec = 'Affliction'
        case 'Demonology':
            role = Role.RANGED
            wow_class = WowClass.WARLOCK
            spec = 'Demonology'
        case 'Destruction':
            role = Role.RANGED
            wow_class = WowClass.WARLOCK
            spec = 'Destruction'
        case 'Discipline':
            role = Role.HEALERS
            wow_class = WowClass.PRIEST
            spec = 'Discipline'
        case 'Holy':
            role = Role.HEALERS
            wow_class = WowClass.PRIEST
            spec = 'Holy'
        case 'Shadow':
            role = Role.RANGED
            wow_class = WowClass.PRIEST
            spec = 'Shadow'
        case 'Elemental':
            role = Role.RANGED
            wow_class = WowClass.SHAMAN
            spec = 'Elemental'
        case 'Restoration1':
            role = Role.HEALERS
            wow_class = WowClass.SHAMAN
            spec = 'Restoration'
        case 'Enhancement':
            role = Role.MELEE
            wow_class = WowClass.SHAMAN
            spec = 'Enhancement'
        case _:
            print(f'WE DID NOT FIND INFO FOR THIS ROLE {spec}')
            role = Role.TANKS
            wow_class = WowClass.PRIEST
            spec = 'Unknown'
    return role, wow_class, spec
