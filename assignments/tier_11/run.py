from copy import deepcopy

from assignments.tier_11.alakir import AlAkir
from assignments.tier_11.chimaeron import Chimaeron
from assignments.tier_11.conclave import Conclave
from google_sheets import SHEET_ID, clear_format
from roster import RaidRoster


def run(raid_id: int):
    """Run function for tier 11"""
    roster = RaidRoster.from_raid_plan(raid_id)
    clear_format(SHEET_ID)
    roster.conditional_format()
    # for Boss in [AlAkir, Chimaeron]:
    for Boss in [Conclave]:
        boss = Boss(roster=deepcopy(roster))
        boss.get_assignments()
        boss.optimize()
        boss.write()
