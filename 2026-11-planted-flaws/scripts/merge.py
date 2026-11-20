#!/usr/bin/env python3
"""Merge the per-session databases in results/runs/ into results/events.sqlite (session ids are distinct)."""
import sqlite3
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
out = ROOT / "results" / "events.sqlite"
if out.exists(): out.unlink()
dst = sqlite3.connect(out)
dst.execute("""create table events(id integer primary key autoincrement, session int, ts real, kind text, agent text, reply_to int, seen_upto int, head int, text text, meta text)""")
for f in sorted((ROOT / "results" / "runs").glob("s*.sqlite"), key=lambda p: int(p.stem[1:])):
    src = sqlite3.connect(f)
    rows = src.execute("select session,ts,kind,agent,reply_to,seen_upto,head,text,meta from events order by id").fetchall()
    dst.executemany("insert into events(session,ts,kind,agent,reply_to,seen_upto,head,text,meta) values(?,?,?,?,?,?,?,?,?)", rows)
dst.commit(); print("merged", dst.execute("select count(distinct session), count(*) from events").fetchone())
