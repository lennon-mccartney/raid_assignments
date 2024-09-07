from __future__ import annotations

from roster import Raider, Role


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
            if raider.role == Role.HEALERS:
                return True
        return False
