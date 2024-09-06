from __future__ import annotations
import os.path
from collections.abc import Generator
from enum import Enum

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import BaseModel

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID and range of a sample spreadsheet.
SHEET_ID = "1YV8zgVa-QC0t5eEAKqoL-5u21uJkDsSOd2RC_b_KY6Y"
ROSTER_RANGE = "data_Raid!H2:R26"


class Role(Enum):
    TANK = '598989638098747403'
    MELEE_DPS = '734439523328720913'
    HEALER = '592438128057253898'
    RANGED_DPS = '592446395596931072'


class Raider(BaseModel):
    party: int
    slot: int
    name: str
    discord_id: int
    wow_class: str
    spec: str
    role: str
    color: str
    position_set: bool = False


class Assignment(list[Raider]):
    def __eq__(self, other: Assignment | int):
        if isinstance(other, int):
            return len(self) == other
        return len(self) == len(other)

    def __gt__(self, other: Assignment | int):
        if isinstance(other, int):
            return len(self) > other
        return len(self) > len(other)

    def __lt__(self, other: Assignment | int):
        if isinstance(other, int):
            return len(self) < other
        return len(self) < len(other)

    def __ge__(self, other: Assignment | int):
        if isinstance(other, int):
            return len(self) >= other
        return len(self) >= len(other)

    def __le__(self, other: Assignment | int):
        if isinstance(other, int):
            return len(self) <= other
        return len(self) <= len(other)

    def has_healer(self) -> bool:
        for raider in self:
            if raider.role == Role.HEALER.value:
                return True
        return False

class AlAkir(BaseModel):
    roster: 'RaidRoster'
    skull: Assignment = Assignment()
    cross: Assignment = Assignment()
    square: Assignment = Assignment()
    moon: Assignment = Assignment()
    triangle: Assignment = Assignment()
    star: Assignment = Assignment()
    diamond: Assignment = Assignment()
    circle: Assignment = Assignment()
    _cells: list[list[str]] | None = None

    class Config:
        arbitrary_types_allowed = True

    def add_to_position(self, position: str|Assignment, raider: str|Raider) -> None:
        if isinstance(raider, str):
            raider = self.roster.get_raider_by_name(raider)
        if isinstance(position, str):
            position = getattr(self, position)

        if not raider:
            return

        position.append(raider)
        raider.position_set = True

    def get_assignments(self):
        for raider in self.roster:
            raider.position_set = False
        self._cells = get_range(SHEET_ID, 'TotFW Assigns!Q70:AR84')
        for i in range(1, 7):
            self.add_to_position('skull', self._cells[i][1])
            self.add_to_position('star', self._cells[i][8])
            self.add_to_position('diamond', self._cells[i][15])
            self.add_to_position('cross', self._cells[i][22])

        for i in range(9, 15):
            self.add_to_position('triangle', self._cells[i][1])
            self.add_to_position('square', self._cells[i][8])
            self.add_to_position('moon', self._cells[i][15])
            self.add_to_position('circle', self._cells[i][22])

    def assignment_to_cells(self, assignment: Assignment, index: int, start: int) -> None:
        i = 0
        for raider in assignment:
            self._cells[start][index] = raider.name
            i += 1
            start += 1
        while i < 6:
            self._cells[start][index] = ''
            i += 1

    def write(self):
        if not getattr(self, '_cells', None):
            self._cells = get_range(SHEET_ID, 'TotFW Assigns!Q70:AR84')
        self.assignment_to_cells(self.skull, 1, 1)
        self.assignment_to_cells(self.star, 8, 1)
        self.assignment_to_cells(self.diamond, 15, 1)
        self.assignment_to_cells(self.cross, 22, 1)
        self.assignment_to_cells(self.triangle, 1, 9)
        self.assignment_to_cells(self.square, 8, 9)
        self.assignment_to_cells(self.moon, 15, 9)
        self.assignment_to_cells(self.circle, 22, 9)
        write_range(SHEET_ID, 'TotFW Assigns!Q70:AR84', self._cells)

    def reset_assignments(self) -> None:
        self.skull = Assignment()
        self.cross = Assignment()
        self.square = Assignment()
        self.moon = Assignment()
        self.triangle = Assignment()
        self.star = Assignment()
        self.diamond = Assignment()
        self.circle = Assignment()
        for raider in self.roster:
            raider.position_set = False

    @staticmethod
    def _this_weird_fucking_tier_system(tiers: list[Assignment]) -> Assignment | None:
        assert len(tiers) == 5
        one, two, three, four, five = tiers
        if one < 3 and one <= two and one <= three:
            return one
        elif two < 3 and two <= three:
            return two
        elif three < 3:
            return three
        elif four < 3:
            return four
        elif five < 3:
            return five
        elif one < 4:
            return one
        elif two < 4:
            return two
        elif three < 4:
            return three
        elif four < 4:
            return four
        elif five < 4:
            return five
        return None

    def get_next_available_melee_spot(self) -> Assignment:
        spot = self._this_weird_fucking_tier_system([self.triangle, self.diamond, self.cross, self.star, self.square])
        if spot is not None:
            return spot
        return self.get_next_available_ranged_spot()

    def get_next_available_ranged_spot(self) -> Assignment:
        spot = self._this_weird_fucking_tier_system([self.skull, self.moon, self.circle, self.square, self.star])
        if spot is not None:
            return spot
        return self.get_next_available_melee_spot()

    def get_next_healer_spot(self) -> Assignment:
        if self.skull < 3 and not self.skull.has_healer(): return self.skull
        if self.diamond < 3 and not self.diamond.has_healer(): return self.diamond
        if self.moon < 3 and not self.moon.has_healer(): return self.moon
        if self.triangle < 3 and not self.triangle.has_healer(): return self.triangle
        if self.star < 3 and not self.star.has_healer(): return self.star
        if self.square < 3 and not self.square.has_healer(): return self.square
        if self.circle < 3 and not self.circle.has_healer(): return self.circle
        if self.cross < 3 and not self.cross.has_healer(): return self.cross

    def get_any_spot(self) -> Assignment:
        # TODO: This
        return self.circle

    def fully_optimize(self) -> None:
        self.reset_assignments()
        self.optimize()

    def optimize(self) -> None:
        main_tank = self.roster.get_main_tank()
        if not main_tank.position_set:
            self.add_to_position('circle', self.roster.get_main_tank())
        for shaman in self.roster.get_enhancement_shamans():
            if not shaman.position_set:
                self.add_to_position(self.get_next_available_melee_spot(), shaman)
        for shaman in self.roster.get_elemental_shamans():
            if not shaman.position_set:
                self.add_to_position(self.get_next_available_ranged_spot(), shaman)
        for healer in self.roster.get_healers():
            if not healer.position_set:
                self.add_to_position(self.get_next_healer_spot(), healer)
        for dk in self.roster.get_dks():
            if not dk.position_set:
                if self.cross < 3:
                    self.add_to_position(self.cross, dk)
                else:
                    self.add_to_position(self.get_next_available_melee_spot(), dk)
        for raider in self.roster.get_melee():
            if not raider.position_set:
                self.add_to_position(self.get_next_available_melee_spot(), raider)
        for raider in self.roster.get_ranged():
            if not raider.position_set:
                self.add_to_position(self.get_next_available_ranged_spot(), raider)
        for raider in self.roster:
            if not raider.position_set:
                self.add_to_position(self.get_next_available_melee_spot(), raider)


class RaidRoster(BaseModel):
    raiders: list[Raider]

    def __iter__(self):
        return self.raiders.__iter__()

    def add_raider(self, raider: Raider) -> None:
        self.raiders.append(raider)

    def get_raider_by_name(self, name: str) -> Raider:
        return next((x for x in self.raiders if x.name == name), None)

    def get_tanks(self) -> list[Raider]:
        tanks = []
        for raider in self.raiders:
            if raider.role == Role.TANK.value:
                tanks.append(raider)
        return tanks

    def get_main_tank(self) -> Raider:
        tanks = self.get_tanks()
        main_tank = next((x for x in tanks if x.spec == 'Blood_Tank'), None)
        if not main_tank:
            main_tank = next((x for x in tanks if x.spec == 'Feral Bear'), None)
        if not main_tank:
            raise Exception('youre fucked  why arnet you running a meta tank')
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
            if raider.wow_class == 'Death Knight':
                yield raider

    def get_healers(self) -> Generator[Raider]:
        for raider in self.raiders:
            if raider.role == Role.HEALER.value:
                yield raider

    def get_melee(self) -> Generator[Raider]:
        for raider in self.raiders:
            if raider.role == Role.MELEE_DPS.value:
                yield raider

    def get_ranged(self) -> Generator[Raider]:
        for raider in self.raiders:
            if raider.role == Role.RANGED_DPS.value:
                yield raider


def get_credentials():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


def get_range(sheet_id: str, cell_range: str) -> list[list[any]]:
    creds = get_credentials()
    # try:
    service = build("sheets", "v4", credentials=creds)

    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=sheet_id, range=cell_range)
        .execute()
    )
    return result.get("values")


def write_range(sheet_id: str, cell_range: str, cells = list[list[any]]) -> None:
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    sheet.values().update(
        spreadsheetId=sheet_id,
        range=cell_range,
        valueInputOption='RAW',
        body={'majorDimension': 'ROWS', 'values': cells},
    ).execute()


def format_cells(sheet_id: str, cell_range: str, cells: list[list[str]]) -> None:
    pass

def main():
    values = get_range(SHEET_ID, ROSTER_RANGE)

    roster = RaidRoster(raiders=[])
    for row in values:
        roster.add_raider(Raider(
            party=row[0],
            slot=row[1],
            name=row[2],
            discord_id=row[3] if row[3] else 4,
            wow_class=row[4],
            spec=row[5],
            role=Role(row[6]),
            color=row[7],
        ))

    with open('raids.json', 'w') as file:
        file.write(roster.model_dump_json())

    alakir = AlAkir(roster=roster)
    alakir.fully_optimize()
    alakir.write()


if __name__ == "__main__":
    main()
