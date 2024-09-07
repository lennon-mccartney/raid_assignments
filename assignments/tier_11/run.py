from copy import deepcopy

from assignments.tier_11.alakir import AlAkir
from roster import RaidRoster


def run(raid_id: int):
    """Run function for tier 11"""
    roster = RaidRoster.from_raid_plan(raid_id)
    for Boss in [AlAkir]:
        boss = Boss(roster=deepcopy(roster))
        boss.get_assignments()
        boss.optimize()
        boss.write()
