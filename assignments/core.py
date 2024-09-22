from __future__ import annotations

from roster import Raider, Role, WowClass


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

    def has_healer(self, flex=0) -> bool:
        for raider in self:
            if raider.role == Role.HEALERS:
                return True
            elif raider.flex_healer is not None and raider.flex_healer < flex:
                return True
        return False

    def healer_count(self, flex=0) -> int:
        return len([x for x in self if x is not None and (x.role == Role.HEALERS or x.flex_healer is not None and x.flex_healer < flex)])

    def has_death_knight(self) -> bool:
        for raider in self:
            if raider.wow_class == WowClass.DEATH_KNIGHT.value:
                return True
        return False

    def has_druid(self, spec: str) -> bool:
        for raider in self:
            if raider.wow_class == WowClass.DRUID.value:
                if not spec:
                    return True
                elif raider.spec == spec:
                    return True
        return False

    def has_warrior(self) -> bool:
        for raider in self:
            if raider.wow_class == WowClass.WARRIOR.value:
                return True
        return False

    def has_paladin(self, spec: str) -> bool:
        for raider in self:
            if raider.wow_class == WowClass.PALADIN.value:
                if not spec:
                    return True
                elif raider.spec == spec:
                    return True
        return False
