from __future__ import annotations

from assignments.tier_11.alakir import AlAkir
from assignments.tier_11.run import run
from google_sheets import ROSTER_RANGE, SHEET_ID, get_range
from roster import RaidRoster, Raider, Role


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
    run(1283260754786517025)
    # main()
    # print(response.json())