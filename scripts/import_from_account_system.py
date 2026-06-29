#!/usr/bin/env python3
"""Import Twitter accounts from Account System API into digital_employees."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.account_system.client import AccountSystemClient
from app.database import SessionLocal, init_db
from app.employee_utils import build_twitter_credentials, dump_credentials, next_employee_code
from app.migrate_schema import migrate_schema
from app.models import DigitalEmployee, EmployeeStage, User

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_USERNAMES = """
Jazzy1527Julie
olyachech
Jump_Yuu
MikeSemczuk
odi_muhammed
Taylormon69
yuki34689842
mrshourback
minmi5417
EsquilantJochen
matan123431
omomonom
seangoodner
jazmat
Bluemagicrose
tylor1967
vpsanand
Kimur11Singeki
Richosena
pakim_7
AariueQ2BE7uWAP
001_xxxshi
_sanzoo
rachaelbateup17
John_Paul_anime
paquittooo33
october3_aki
nalbatfuat37
taroro36
a8031am
Oll3s_
weirdeel
anantec19
daazs98
torisauresrex
otkmoe
Lovelencja
moleshar
mga__lo
lopez_valer
a_mehtab_razzaq
mur_claudio
SKramny
leilani98430971
suzukisandani
GeorginaMFisch2
mobihasan
LauraineLee
DIRTYLILREBEL
RUNA___desu
theceejinator
hloniphilem1
natasha96369772
pf5kari
mimuravpjcojp
gDtet9CappBCTCe
office23104342
mo_yamoyashi
JennnaNicholson
RubachScott
""".strip().split()


async def fetch_all(client: AccountSystemClient, usernames: list[str]) -> dict[str, str | Exception]:
    out: dict[str, str | Exception] = {}

    async def one(name: str) -> None:
        try:
            out[name] = await client.fetch_cookie(name)
        except Exception as e:
            out[name] = e

    await asyncio.gather(*(one(u) for u in usernames))
    return out


def import_to_db(
    cookies: dict[str, str | Exception],
    *,
    owner_email: str,
    employee_type: str,
) -> tuple[int, int, int]:
    init_db()
    migrate_schema()
    db = SessionLocal()
    ok = skip = fail = 0
    try:
        owner = db.query(User).filter(User.email == owner_email).first()
        if not owner:
            raise SystemExit(f"Owner user not found: {owner_email}")

        for username, result in cookies.items():
            handle = f"@{username}"
            existing = (
                db.query(DigitalEmployee)
                .filter(DigitalEmployee.owner_user_id == owner.id, DigitalEmployee.twitter_handle == handle)
                .first()
            )
            if existing:
                skip += 1
                logger.info("%s — skip exists %s", username, existing.code)
                continue
            if isinstance(result, Exception):
                fail += 1
                logger.error("%s — fetch failed: %s", username, result)
                continue
            emp = DigitalEmployee(
                code=next_employee_code(db),
                display_name=username,
                role_title=employee_type,
                platform="twitter",
                twitter_handle=handle,
                credentials=dump_credentials(build_twitter_credentials(result)),
                stage=EmployeeStage.recruiting,
                owner_user_id=owner.id,
            )
            db.add(emp)
            db.flush()
            ok += 1
            logger.info("%s — imported %s", username, emp.code)
        db.commit()
    finally:
        db.close()
    return ok, skip, fail


async def main_async(args: argparse.Namespace) -> None:
    client = AccountSystemClient()
    if not client.configured:
        raise SystemExit("Set ACCOUNT_SYSTEM_API_KEY in environment")

    usernames = Path(args.file).read_text().splitlines() if args.file else DEFAULT_USERNAMES
    usernames = [u.strip() for u in usernames if u.strip()]
    logger.info("Fetching cookies for %s accounts…", len(usernames))
    cookies = await fetch_all(client, usernames)
    ok, skip, fail = import_to_db(
        cookies,
        owner_email=args.owner,
        employee_type=args.type,
    )
    logger.info("Done: imported=%s skip=%s fail=%s", ok, skip, fail)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file")
    parser.add_argument("--owner", default="admin@spreadx.ai")
    parser.add_argument("--type", default="twitter_operator", choices=["twitter_operator", "twitter_engagement"])
    asyncio.run(main_async(parser.parse_args()))


if __name__ == "__main__":
    main()
