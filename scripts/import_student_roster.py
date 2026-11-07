import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from app import create_app
from app.extensions import db
from app.models import Domain, Team, TeamMember, User

ROSTER_PATH = ROOT / "data" / "student_roster.csv"
TEAM_DOMAINS = {
    **{f"FT_{number:02d}": ("D05", "Neural Techgenix (AI) Group") for number in range(1, 9)},
    **{f"FT_{number:02d}": ("D02", "CodeWave Group") for number in range(9, 15)},
    **{f"FT_{number:02d}": ("D03", "Cyber Security Group") for number in range(15, 19)},
    **{f"FT_{number:02d}": ("D04", "Data Science Group") for number in range(19, 25)},
    **{f"FT_{number:02d}": ("D01", "IoT & Robotics / Multimedia Group") for number in range(25, 28)},
}


def load_roster():
    with ROSTER_PATH.open(encoding="utf-8-sig", newline="") as roster_file:
        rows = list(csv.DictReader(roster_file))

    required_headers = {"team_id", "student_id", "name", "role"}
    if not rows or set(rows[0]) != required_headers:
        raise ValueError(f"{ROSTER_PATH} must contain {sorted(required_headers)}.")

    student_ids = [row["student_id"].strip() for row in rows]
    if len(student_ids) != len(set(student_ids)):
        raise ValueError("Student IDs must be unique.")

    leaders = Counter()
    teams = set()
    for row in rows:
        row["team_id"] = row["team_id"].strip().upper()
        row["student_id"] = row["student_id"].strip().upper()
        row["name"] = row["name"].strip()
        row["role"] = row["role"].strip().title()
        if row["team_id"] not in TEAM_DOMAINS:
            raise ValueError(f"Unknown team ID: {row['team_id']}")
        if not row["name"] or not row["student_id"]:
            raise ValueError("Every roster row must have a name and student ID.")
        if row["role"] not in {"Leader", "Member"}:
            raise ValueError(f"Invalid role for {row['student_id']}: {row['role']}")
        if not all(character.isalnum() or character in "_/-" for character in row["student_id"]):
            raise ValueError(f"Invalid student ID: {row['student_id']}")
        teams.add(row["team_id"])
        leaders[row["team_id"]] += row["role"] == "Leader"

    expected_teams = set(TEAM_DOMAINS)
    if teams != expected_teams:
        raise ValueError(f"Roster must include every team; missing: {sorted(expected_teams - teams)}")
    if any(leaders[team_id] != 1 for team_id in expected_teams):
        raise ValueError("Each team must have exactly one leader.")
    return rows


def import_roster(rows, app):
    with app.app_context():
        teams = {team.team_code: team for team in Team.query.all()}
        domains = {domain.code: domain for domain in Domain.query.all()}
        if set(TEAM_DOMAINS) - set(teams) or {value[0] for value in TEAM_DOMAINS.values()} - set(domains):
            raise ValueError("Seed the 27 teams and five domains before importing the roster.")

        grouped_rows = defaultdict(list)
        for row in rows:
            grouped_rows[row["team_id"]].append(row)

        for team_code, roster_rows in grouped_rows.items():
            team = teams[team_code]
            domain_code, domain_name = TEAM_DOMAINS[team_code]
            domain = domains[domain_code]
            if domain.name != domain_name:
                raise ValueError(f"Domain {domain_code} does not match the roster mapping.")
            team.domain_id = domain.id
            leader = next(row for row in roster_rows if row["role"] == "Leader")
            team.leader_name = leader["name"]

        for row in rows:
            team = teams[row["team_id"]]
            username = row["student_id"]
            user = User.query.filter_by(username=username).first()
            initialize_password = user is None
            if user is None and row["role"] == "Leader":
                user = User.query.filter_by(
                    role="team_leader",
                    team_id=team.id,
                ).first()
                initialize_password = user is not None
            if user is None:
                user = User(
                    username=username,
                    role="team_member",
                    display_name=row["name"],
                    team_id=team.id,
                )
                db.session.add(user)
            elif user.team_id not in {None, team.id}:
                raise ValueError(f"{username} is already assigned to a different team.")

            user.username = username
            user.role = "team_leader" if row["role"] == "Leader" else "team_member"
            user.display_name = row["name"]
            user.team_id = team.id
            if initialize_password:
                user.set_password(row["team_id"])
            db.session.flush()

            member = TeamMember.query.filter_by(prn=username).first()
            if member and member.user_id not in {None, user.id}:
                raise ValueError(f"{username} is already linked to a different login.")
            if member is None:
                member = TeamMember(team_id=team.id, full_name=row["name"], prn=username)
                db.session.add(member)
            member.team_id = team.id
            member.full_name = row["name"]
            member.prn = username
            member.user = user

        db.session.commit()
        return len(rows)


def main():
    parser = argparse.ArgumentParser(description="Import the FUTURE-TECH student roster.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Create/update student accounts in the configured database.",
    )
    args = parser.parse_args()
    rows = load_roster()
    if not args.apply:
        print(f"Validated {len(rows)} students across {len(TEAM_DOMAINS)} teams.")
        print("Run with --apply to import student accounts and set their initial passwords.")
        return
    app = create_app()
    imported = import_roster(rows, app)
    print(f"Imported {imported} student accounts across {len(TEAM_DOMAINS)} teams.")
    print("Student username: Student_ID; initial password: Team_ID.")


if __name__ == "__main__":
    main()
