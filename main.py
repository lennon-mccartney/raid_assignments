import os.path
from collections.abc import generator
from enum import Enum

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import BaseModel

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

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
    position_set: bool = False


class Assignment(list):
    def __eq__(self, other: 'Assignment'|int):
        if isinstance(other, int):
            return len(self) == other
        return len(self) == len(other)

    def __gt__(self, other: 'Assignment'|int):
        if isinstance(other, int):
            return len(self) > other
        return len(self) > len(other)

    def __lt__(self, other: 'Assignment'|int):
        if isinstance(other, int):
            return len(self) < other
        return len(self) < len(other)


class AlAkir:
    roster: 'RaidRoster'
    skull: Assignment[Raider] = Assignment()
    cross: Assignment[Raider] = Assignment()
    square: Assignment[Raider] = Assignment()
    moon: Assignment[Raider] = Assignment()
    triangle: Assignment[Raider] = Assignment()
    star: Assignment[Raider] = Assignment()
    diamond: Assignment[Raider] = Assignment()
    circle: Assignment[Raider] = Assignment()

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
        raw_assignments = get_range(SHEET_ID, 'TotFW Assigns!Q70:AR84')
        for i in range(1, 7):
            self.add_to_position('skull', raw_assignments[i][1])
            self.add_to_position('star', raw_assignments[i][8])
            self.add_to_position('diamond', raw_assignments[i][15])
            self.add_to_position('cross', raw_assignments[i][22])

        for i in range(10, 16):
            self.add_to_position('triangle', raw_assignments[i][1])
            self.add_to_position('square', raw_assignments[i][8])
            self.add_to_position('moon', raw_assignments[i][15])
            self.add_to_position('circle', raw_assignments[i][22])

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

    def _this_weird_fucking_tier_system(self, tiers: list[Assignment]):
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
        return self.get_any_spot()

    def get_next_available_melee_spot(self) -> Assignment:
        return self._this_weird_fucking_tier_system([self.triangle, self.diamond, self.cross, self.star, self.square])

    def get_next_available_ranged_spot(self) -> Assignment:
        return self._this_weird_fucking_tier_system([self.skull, self.moon, self.circle, self.square, self.star])

    def get_next_healer_spot(self) -> generator[Assignment]:
        if self.skull < 3: yield self.skull
        if self.diamond < 3: yield self.diamond
        if self.moon < 3: yield self.moon
        if self.triangle < 3: yield self.triangle
        if self.star < 3: yield self.star
        if self.square < 3: yield self.square
        if self.circle < 3: yield self.circle
        if self.cross < 3: yield self.cross
        raise StopIteration()

    def get_any_spot(self) -> Assignment:
        # TODO: This
        return self.circle

    def fully_optimize(self) -> None:
        self.reset_assignments()
        self.add_to_position('circle', self.roster.get_main_tank())
        for shaman in self.roster.get_enhancement_shamans():
            self.add_to_position(self.get_next_available_melee_spot(), shaman)
        for shaman in self.roster.get_elemental_shamans():
            self.add_to_position(self.get_next_available_ranged_spot(), shaman)
        for healer in self.roster.get_healers():
            self.add_to_position(self.get_next_healer_spot(), healer)


class RaidRoster(BaseModel):
    raiders: list[Raider]

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

    def get_enhancement_shamans(self) -> generator[Raider]:
        for raider in self.raiders:
            if raider.spec == 'Enhancement':
                yield raider

    def get_elemental_shamans(self) -> generator[Raider]:
        for raider in self.raiders:
            if raider.spec == 'Elemental':
                yield raider

    def get_healers(self) -> generator[Raider]:
        for raider in self.raiders:
            if raider.role == Role.HEALER.value:
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


def main():
    # values = get_range(SHEET_ID, ROSTER_RANGE)
    #
    # roster = RaidRoster(raiders=[])
    # for row in values:
    #     roster.add_raider(Raider(
    #         party=row[0],
    #         slot=row[1],
    #         name=row[2],
    #         discord_id=row[3] if row[3] else 4,
    #         wow_class=row[4],
    #         spec=row[5],
    #         role=Role(row[6]),
    #     ))
    #
    # print(roster.has_blood_dk())
    # with open('raids.json', 'w') as file:
    #     file.write(roster.model_dump_json())

    alakir = AlAkir()
    print(alakir.get_assignments())

if __name__ == "__main__":
    main()
