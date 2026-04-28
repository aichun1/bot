import aiosqlite
import json
from datetime import datetime
from typing import Optional, List

DB_PATH = "superbot.db"

class Database:
    def __init__(self):
        self.path = DB_PATH

    async def init(self):
        async with aiosqlite.connect(self.path) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    user_id     INTEGER PRIMARY KEY,
                    username    TEXT,
                    authed      INTEGER DEFAULT 0,
                    authed_at   TEXT,
                    last_seen   TEXT
                );

                CREATE TABLE IF NOT EXISTS blacklist (
                    chat_id     TEXT PRIMARY KEY,
                    label       TEXT,
                    added_at    TEXT
                );

                CREATE TABLE IF NOT EXISTS scheduled_msgs (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id     TEXT NOT NULL,
                    message     TEXT NOT NULL,
                    send_at     TEXT NOT NULL,
                    done        INTEGER DEFAULT 0,
                    created_at  TEXT
                );

                CREATE TABLE IF NOT EXISTS monitors (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id     TEXT NOT NULL,
                    keyword     TEXT NOT NULL,
                    active      INTEGER DEFAULT 1,
                    created_at  TEXT
                );

                CREATE TABLE IF NOT EXISTS autoreply (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    active      INTEGER DEFAULT 0,
                    reply_text  TEXT DEFAULT 'Hozir band, keyinroq javob beraman.',
                    updated_at  TEXT
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key         TEXT PRIMARY KEY,
                    value       TEXT
                );
            """)
            await db.commit()

        # Default autoreply row
        await self.execute(
            "INSERT OR IGNORE INTO autoreply(id, active, reply_text, updated_at) VALUES(1, 0, 'Hozir band, keyinroq javob beraman.', ?)",
            (datetime.now().isoformat(),)
        )

    async def execute(self, sql: str, params=()) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(sql, params)
            await db.commit()

    async def fetchone(self, sql: str, params=()) -> Optional[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(sql, params)
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def fetchall(self, sql: str, params=()) -> List[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(sql, params)
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    # ---------- AUTH ----------
    async def is_authed(self, user_id: int) -> bool:
        row = await self.fetchone("SELECT authed FROM sessions WHERE user_id=?", (user_id,))
        return bool(row and row["authed"])

    async def set_auth(self, user_id: int, username: str, authed: bool):
        now = datetime.now().isoformat()
        await self.execute("""
            INSERT INTO sessions(user_id, username, authed, authed_at, last_seen)
            VALUES(?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                authed=excluded.authed,
                authed_at=excluded.authed_at,
                last_seen=excluded.last_seen
        """, (user_id, username or "", int(authed), now, now))

    async def update_last_seen(self, user_id: int):
        await self.execute(
            "UPDATE sessions SET last_seen=? WHERE user_id=?",
            (datetime.now().isoformat(), user_id)
        )

    # ---------- BLACKLIST ----------
    async def blacklist_add(self, chat_id: str, label: str = ""):
        await self.execute(
            "INSERT OR REPLACE INTO blacklist(chat_id, label, added_at) VALUES(?,?,?)",
            (chat_id, label, datetime.now().isoformat())
        )

    async def blacklist_remove(self, chat_id: str):
        await self.execute("DELETE FROM blacklist WHERE chat_id=?", (chat_id,))

    async def blacklist_get(self) -> List[dict]:
        return await self.fetchall("SELECT * FROM blacklist")

    async def is_blacklisted(self, chat_id: str) -> bool:
        row = await self.fetchone("SELECT 1 FROM blacklist WHERE chat_id=?", (chat_id,))
        return row is not None

    # ---------- SCHEDULE ----------
    async def schedule_add(self, chat_id: str, message: str, send_at: str) -> int:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "INSERT INTO scheduled_msgs(chat_id, message, send_at, created_at) VALUES(?,?,?,?)",
                (chat_id, message, send_at, datetime.now().isoformat())
            )
            await db.commit()
            return cur.lastrowid

    async def schedule_pending(self) -> List[dict]:
        return await self.fetchall(
            "SELECT * FROM scheduled_msgs WHERE done=0 AND send_at <= ? ORDER BY send_at",
            (datetime.now().isoformat(),)
        )

    async def schedule_mark_done(self, msg_id: int):
        await self.execute("UPDATE scheduled_msgs SET done=1 WHERE id=?", (msg_id,))

    async def schedule_list(self) -> List[dict]:
        return await self.fetchall("SELECT * FROM scheduled_msgs WHERE done=0 ORDER BY send_at")

    # ---------- MONITOR ----------
    async def monitor_add(self, chat_id: str, keyword: str):
        await self.execute(
            "INSERT INTO monitors(chat_id, keyword, active, created_at) VALUES(?,?,1,?)",
            (chat_id, keyword, datetime.now().isoformat())
        )

    async def monitor_list(self) -> List[dict]:
        return await self.fetchall("SELECT * FROM monitors WHERE active=1")

    async def monitor_remove(self, monitor_id: int):
        await self.execute("UPDATE monitors SET active=0 WHERE id=?", (monitor_id,))

    # ---------- AUTOREPLY ----------
    async def get_autoreply(self) -> dict:
        return await self.fetchone("SELECT * FROM autoreply WHERE id=1")

    async def set_autoreply(self, active: bool, text: str):
        await self.execute(
            "UPDATE autoreply SET active=?, reply_text=?, updated_at=? WHERE id=1",
            (int(active), text, datetime.now().isoformat())
        )

    # ---------- SETTINGS ----------
    async def set_setting(self, key: str, value: str):
        await self.execute(
            "INSERT OR REPLACE INTO settings(key, value) VALUES(?,?)", (key, value)
        )

    async def get_setting(self, key: str, default=None) -> Optional[str]:
        row = await self.fetchone("SELECT value FROM settings WHERE key=?", (key,))
        return row["value"] if row else default
