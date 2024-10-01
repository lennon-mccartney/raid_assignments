from copy import deepcopy

from assignments.tier_12.shannox import Shannox
from google_sheets import clear_format, format_cells
from roster import RaidRoster


def run(raid_id: int, sheet_id: str, gids: list[str]):
    """Run function for tier 12"""
    roster = RaidRoster.from_raid_plan(raid_id)
    # clear_format(sheet_id)
    # roster.conditional_format(sheet_id, gids)
    for Boss in [Shannox]:
        boss = Boss(roster=deepcopy(roster))
        boss.get_assignments()
        boss.optimize()
        boss.write(sheet_id)
