from pydantic import BaseModel

from google_sheets import SHEET_ID, get_range, write_range
from roster import RaidRoster, Raider


class Chimaeron(BaseModel):
    roster: RaidRoster
    melee_one: Raider | None = None
    melee_two: Raider | None = None
    melee_three: Raider | None = None
    melee_four: Raider | None = None
    melee_five: Raider | None = None
    melee_six: Raider | None = None
    melee_seven: Raider | None = None
    melee_eight: Raider | None = None
    melee_nine: Raider | None = None
    melee_ten: Raider | None = None
    ranged_one: Raider | None = None
    ranged_two: Raider | None = None
    ranged_three: Raider | None = None
    ranged_four: Raider | None = None
    ranged_five: Raider | None = None
    ranged_six: Raider | None = None
    ranged_seven: Raider | None = None
    ranged_eight: Raider | None = None
    ranged_nine: Raider | None = None
    ranged_ten: Raider | None = None
    ranged_eleven: Raider | None = None
    ranged_twelve: Raider | None = None
    ranged_thirteen: Raider | None = None
    ranged_fourteen: Raider | None = None
    ranged_fifteen: Raider | None = None

    _cells: list[list[str]] | None = None
    flex_healers: int = 0

    def get_melee_spot(self):
        if not self.melee_five:
            return 'melee_five'
        elif not self.melee_six:
            return 'melee_six'
        elif not self.melee_seven:
            return 'melee_seven'
        elif not self.melee_three:
            return 'melee_three'
        elif not self.melee_eight:
            return 'melee_eight'
        elif not self.melee_four:
            return 'melee_four'
        elif not self.melee_nine:
            return 'melee_nine'
        elif not self.melee_two:
            return 'melee_two'
        elif not self.melee_ten:
            return 'melee_ten'
        elif not self.melee_one:
            return 'melee_one'
        else:
            return self.get_ranged_spot()

    def get_ranged_spot(self):
        if not self.ranged_four:
            return 'ranged_four'
        elif not self.ranged_five:
            return 'ranged_five'
        elif not self.ranged_three:
            return 'ranged_three'
        elif not self.ranged_six:
            return 'ranged_six'
        elif not self.ranged_two:
            return 'ranged_two'
        elif not self.ranged_seven:
            return 'ranged_seven'
        elif not self.ranged_twelve:
            return 'ranged_twelve'
        elif not self.ranged_eleven:
            return 'ranged_eleven'
        elif not self.ranged_thirteen:
            return 'ranged_thirteen'
        elif not self.ranged_ten:
            return 'ranged_ten'
        elif not self.ranged_fourteen:
            return 'ranged_fourteen'
        elif not self.ranged_nine:
            return 'ranged_nine'
        elif not self.ranged_fifteen:
            return 'ranged_fifteen'
        elif not self.ranged_one:
            return 'ranged_one'
        elif not self.ranged_eight:
            return 'ranged_eight'
        else:
            return self.get_melee_spot()

    def set_position(self, spot, raider):
        setattr(self, spot, raider)
        raider.position_set = True

    def optimize(self):
        main_tank = self.roster.get_tank(main_tank=True)
        main_tank.position_set = True
        for raider in self.roster.get_rogues():
            if not raider.position_set:
                self.set_position(self.get_melee_spot(), raider)

        for raider in self.roster.get_healers():
            if not raider.position_set:
                self.set_position(self.get_ranged_spot(), raider)

        for raider in self.roster.get_melee():
            if not raider.position_set:
                self.set_position(self.get_melee_spot(), raider)

        for raider in self.roster.get_tanks():
            if not raider.position_set:
                self.set_position(self.get_melee_spot(), raider)

        for raider in self.roster.get_warlocks():
            if not raider.position_set:
                if not self.melee_one:
                    self.set_position('melee_one', raider)
                elif not self.melee_ten:
                    self.set_position('melee_ten', raider)
                elif not self.melee_nine:
                    self.set_position('melee_nine', raider)
                elif not self.melee_two:
                    self.set_position('melee_two', raider)

        for raider in self.roster.get_ranged():
            if not raider.position_set:
                self.set_position(self.get_ranged_spot(), raider)

    def get_assignments(self):
        for raider in self.roster:
            raider.position_set = False
        self._cells = get_range(SHEET_ID, 'BWD Assigns!AV97:BG111')
        self.ranged_one = self.roster.get_raider_by_name(self._cells[0][0])
        if self.ranged_one is not None:
            self.ranged_one.position_set = True
        self.melee_one = self.roster.get_raider_by_name(self._cells[0][-1])
        if self.melee_one is not None:
            self.melee_one.position_set = True
        self.ranged_two = self.roster.get_raider_by_name(self._cells[1][0])
        if self.ranged_two is not None:
            self.ranged_two.position_set = True
        self.melee_two = self.roster.get_raider_by_name(self._cells[1][-1])
        if self.melee_two is not None:
            self.melee_two.position_set = True
        self.ranged_three = self.roster.get_raider_by_name(self._cells[2][0])
        if self.ranged_three is not None:
            self.ranged_three.position_set = True
        self.melee_three = self.roster.get_raider_by_name(self._cells[2][-1])
        if self.melee_three is not None:
            self.melee_three.position_set = True
        self.ranged_four = self.roster.get_raider_by_name(self._cells[3][0])
        if self.ranged_four is not None:
            self.ranged_four.position_set = True
        self.melee_four = self.roster.get_raider_by_name(self._cells[3][-1])
        if self.melee_four is not None:
            self.melee_four.position_set = True
        self.ranged_five = self.roster.get_raider_by_name(self._cells[4][0])
        if self.ranged_five is not None:
            self.ranged_five.position_set = True
        self.melee_five = self.roster.get_raider_by_name(self._cells[4][-1])
        if self.melee_five is not None:
            self.melee_five.position_set = True
        self.ranged_six = self.roster.get_raider_by_name(self._cells[5][0])
        if self.ranged_six is not None:
            self.ranged_six.position_set = True
        self.melee_six = self.roster.get_raider_by_name(self._cells[5][-1])
        if self.melee_six is not None:
            self.melee_six.position_set = True
        self.ranged_seven = self.roster.get_raider_by_name(self._cells[6][0])
        if self.ranged_seven is not None:
            self.ranged_seven.position_set = True
        self.melee_seven = self.roster.get_raider_by_name(self._cells[6][-1])
        if self.melee_seven is not None:
            self.melee_seven.position_set = True
        self.ranged_eight = self.roster.get_raider_by_name(self._cells[7][0])
        if self.ranged_eight is not None:
            self.ranged_eight.position_set = True
        self.melee_eight = self.roster.get_raider_by_name(self._cells[7][-1])
        if self.melee_eight is not None:
            self.melee_eight.position_set = True
        self.ranged_nine = self.roster.get_raider_by_name(self._cells[8][0])
        if self.ranged_nine is not None:
            self.ranged_nine.position_set = True
        self.melee_nine = self.roster.get_raider_by_name(self._cells[8][-1])
        if self.melee_nine is not None:
            self.melee_nine.position_set = True
        self.ranged_ten = self.roster.get_raider_by_name(self._cells[9][0])
        if self.ranged_ten is not None:
            self.ranged_ten.position_set = True
        self.melee_ten = self.roster.get_raider_by_name(self._cells[9][-1])
        if self.melee_ten is not None:
            self.melee_ten.position_set = True
        self.ranged_eleven = self.roster.get_raider_by_name(self._cells[10][0])
        if self.ranged_eleven is not None:
            self.ranged_eleven.position_set = True
        self.ranged_twelve = self.roster.get_raider_by_name(self._cells[11][0])
        if self.ranged_twelve is not None:
            self.ranged_twelve.position_set = True
        self.ranged_thirteen = self.roster.get_raider_by_name(self._cells[12][0])
        if self.ranged_thirteen is not None:
            self.ranged_thirteen.position_set = True
        self.ranged_fourteen = self.roster.get_raider_by_name(self._cells[13][0])
        if self.ranged_fourteen is not None:
            self.ranged_fourteen.position_set = True
        self.ranged_fifteen = self.roster.get_raider_by_name(self._cells[14][0])
        if self.ranged_fifteen is not None:
            self.ranged_fifteen.position_set = True

    def write(self):
        if not self._cells:
            self._cells = get_range(SHEET_ID, 'BWD Assigns!AV97:BG111')
        self._cells[0][0] = self.ranged_one.name if self.ranged_one else 'Empty'
        self._cells[0][-1] = self.melee_one.name if self.melee_one else 'Empty'
        self._cells[1][0] = self.ranged_two.name if self.ranged_two else 'Empty'
        self._cells[1][-1] = self.melee_two.name if self.melee_two else 'Empty'
        self._cells[2][0] = self.ranged_three.name if self.ranged_three else 'Empty'
        self._cells[2][-1] = self.melee_three.name if self.melee_three else 'Empty'
        self._cells[3][0] = self.ranged_four.name if self.ranged_four else 'Empty'
        self._cells[3][-1] = self.melee_four.name if self.melee_four else 'Empty'
        self._cells[4][0] = self.ranged_five.name if self.ranged_five else 'Empty'
        self._cells[4][-1] = self.melee_five.name if self.melee_five else 'Empty'
        self._cells[5][0] = self.ranged_six.name if self.ranged_six else 'Empty'
        self._cells[5][-1] = self.melee_six.name if self.melee_six else 'Empty'
        self._cells[6][0] = self.ranged_seven.name if self.ranged_seven else 'Empty'
        self._cells[6][-1] = self.melee_seven.name if self.melee_seven else 'Empty'
        self._cells[7][0] = self.ranged_eight.name if self.ranged_eight else 'Empty'
        self._cells[7][-1] = self.melee_eight.name if self.melee_eight else 'Empty'
        self._cells[8][0] = self.ranged_nine.name if self.ranged_nine else 'Empty'
        self._cells[8][-1] = self.melee_nine.name if self.melee_nine else 'Empty'
        self._cells[9][0] = self.ranged_ten.name if self.ranged_ten else 'Empty'
        self._cells[9][-1] = self.melee_ten.name if self.melee_ten else 'Empty'
        self._cells[10][0] = self.ranged_eleven.name if self.ranged_eleven else 'Empty'
        self._cells[11][0] = self.ranged_twelve.name if self.ranged_twelve else 'Empty'
        self._cells[12][0] = self.ranged_thirteen.name if self.ranged_thirteen else 'Empty'
        self._cells[13][0] = self.ranged_fourteen.name if self.ranged_fourteen else 'Empty'
        self._cells[14][0] = self.ranged_fifteen.name if self.ranged_fifteen else 'Empty'
        write_range(SHEET_ID, 'BWD Assigns!AV97:BG111', self._cells)
