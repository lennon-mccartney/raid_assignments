from __future__ import annotations

import json
import os

from pydantic import BaseModel

from assignments.core import Assignment
from google_sheets import SHEET_ID, format_cells, get_range, write_range
from roster import RaidRoster, Raider


class AlAkir(BaseModel):
    roster: RaidRoster
    skull: Assignment = Assignment()
    cross: Assignment = Assignment()
    square: Assignment = Assignment()
    moon: Assignment = Assignment()
    triangle: Assignment = Assignment()
    star: Assignment = Assignment()
    diamond: Assignment = Assignment()
    circle: Assignment = Assignment()
    _cells: list[list[str]] | None = None
    flex_healers: int = 0

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, __context):
        if not os.path.exists('saved_responses.json'):
            print('do you want to flex healers for Al\'Akir? (y/n)')
            user_input = input()
            if user_input == 'y':
                print('how many healers do you want to flex?')
                user_input = input()
                flex_healers = int(user_input)
            else:
                flex_healers = 0
            with open('saved_responses.json', 'w') as file:
                file.write(json.dumps({'alakir': {'flex_healers': flex_healers}}))
        with open('saved_responses.json') as file:
            config = json.loads(file.read())
        self.flex_healers = config['alakir']['flex_healers']

    def assignments(self):
        for assignment in [self.skull, self.cross, self.square, self.moon, self.triangle, self.star, self.diamond, self.circle]:
            yield assignment

    def assignment_cells(self):
        for cell in [self.skull_cell, self.cross_cell, self.square_cell, self.moon_cell, self.triangle_cell, self.star_cell, self.diamond_cell, self.circle]:
            yield cell

    def add_to_position(self, position: str | Assignment, raider: str | Raider) -> None:
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
        if self.skull < 3 and not self.skull.has_healer(flex=self.flex_healers): return self.skull
        if self.diamond < 3 and not self.diamond.has_healer(flex=self.flex_healers): return self.diamond
        if self.moon < 3 and not self.moon.has_healer(flex=self.flex_healers): return self.moon
        if self.triangle < 3 and not self.triangle.has_healer(flex=self.flex_healers): return self.triangle
        if self.star < 3 and not self.star.has_healer(flex=self.flex_healers): return self.star
        if self.square < 3 and not self.square.has_healer(flex=self.flex_healers): return self.square
        if self.circle < 3 and not self.circle.has_healer(flex=self.flex_healers): return self.circle
        if self.cross < 3 and not self.cross.has_healer(flex=self.flex_healers): return self.cross

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
            if shaman.flex_healer is not None and shaman.flex_healer < self.flex_healers:
                continue
            if not shaman.position_set:
                self.add_to_position(self.get_next_available_ranged_spot(), shaman)
        for healer in self.roster.get_healers(flex=self.flex_healers):
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
        for tank in self.roster.get_tanks():
            if not tank.position_set:
                self.add_to_position(self.get_next_available_melee_spot(), tank)
        for raider in self.roster.get_ranged():
            if not raider.position_set:
                self.add_to_position(self.get_next_available_ranged_spot(), raider)
        for raider in self.roster:
            if not raider.position_set:
                self.add_to_position(self.get_next_available_melee_spot(), raider)
