import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.json"
STATE_PATH = ROOT / "state.json"
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

AION2HUB_URL = "https://aion2hub.com/tools/event-timer"

SERVER_ZONES = {
    "TW": ZoneInfo("Asia/Taipei"),
    "KR": ZoneInfo("Asia/Seoul"),
}

# Times below are server-local.
RIFT_HOURS = [2, 5, 8, 11, 14, 17, 20, 23]
ABYSS_RIFT_WEEKDAYS = {1, 3}   # Tue, Thu (Mon=0)
ABYSS_EVENT_WEEKDAYS = {2, 5}  # Wed, Sat
ABYSS_HOUR = 22

HOURLY_MINIGAMES = [
    "Defend Shugo Merchants",
    "Goldrin's Treasure",
    "Hidden Lugi",
    "Jump Jump",
    "Mysterious Track",
    "Not This Tile?",
    "Nyerk Shooter",
    "Odyle Flight Frenzy",
    "Shugo's Dilemma",
    "Up! Up! Up!",
    "Wraith Evasion",
]

with CONFIG_PATH.open("r", encoding="utf-8") as f:
    cfg = json.load(f)

if STATE_PATH.exists():
    with STATE_PATH.open("r", encoding="utf-8") as f:
        state = json.load(f)
else:
    state = {"sent": {}}

server = cfg.get("server", "TW").upper()
if server not in SERVER_ZONES:
    raise ValueError("config.json -> server must be TW or KR")

server_tz = SERVER_ZONES[server]
role_id = str(cfg.get("role_id", "")).strip()
warning_minutes = sorted(set(int(x) for x in cfg.get("warning_minutes", [15, 5])), reverse=True)
notify_at_start = bool(cfg.get("notify_at_start", True))
enabled = cfg.get("events", {})

now_utc = datetime.now(timezone.utc)
now_server = now_utc.astimezone(server_tz)


def unix(dt):
    return int(dt.timestamp())


def discord_time(dt):
    ts = unix(dt)
    return f"<t:{ts}:F> · <t:{ts}:R>"


def event_key(event_id, event_time, phase):
    return f"{event_id}:{unix(event_time)}:{phase}"


def already_sent(key):
    return key in state.setdefault("sent", {})


def mark_sent(key):
    state["sent"][key] = now_utc.isoformat()


def role_mention():
    return f"<@&{role_id}>" if role_id else ""


def post_embed(title, description, color=0x7D3CFF):
    payload = {
        "username": "AION 2 Eventos",
        "allowed_mentions": {"parse": ["roles"] if role_id else []},
        "content": role_mention(),
        "embeds": [{
            "title": title,
            "description": description,
            "color": color,
            "url": AION2HUB_URL,
            "footer": {"text": f"AION 2 • Servidor {server} • Datos de horario: AION2Hub"}
        }]
    }
    r = requests.post(WEBHOOK_URL, json=payload, timeout=20)
    r.raise_for_status()


def candidates_daily(hours):
    out = []
    for day_offset in (-1, 0, 1):
        d = (now_server + timedelta(days=day_offset)).date()
        for h in hours:
            out.append(datetime(d.year, d.month, d.day, h, 0, tzinfo=server_tz))
    return out


def candidates_hourly(minute):
    base = now_server.replace(minute=minute, second=0, microsecond=0)
    return [base + timedelta(hours=x) for x in (-1, 0, 1)]


def candidates_weekly(weekdays, hour):
    out = []
    for day_offset in range(-1, 8):
        dtime = now_server + timedelta(days=day_offset)
        if dtime.weekday() in weekdays:
            d = dtime.date()
            out.append(datetime(d.year, d.month, d.day, hour, 0, tzinfo=server_tz))
    return out


def maybe_notify(event_id, event_name, emoji, event_time, details=""):
    delta_min = (event_time - now_server).total_seconds() / 60

    # GitHub scheduled jobs may start a few minutes late. Each notification
    # accepts a 5-minute window, while state.json prevents duplicates.
    for mins in warning_minutes:
        if mins - 5 < delta_min <= mins:
            phase = f"warn{mins}"
            key = event_key(event_id, event_time, phase)
            if not already_sent(key):
                extra = f"\n\n{details}" if details else ""
                post_embed(
                    f"{emoji} {event_name} — ¡Faltan {mins} minutos!",
                    f"**Servidor:** {server}\n"
                    f"**Comienza:** {discord_time(event_time)}"
                    f"{extra}\n\n"
                    f"⚔️ ¡Prepárense, Daevas!"
                )
                mark_sent(key)

    if notify_at_start and -5 <= delta_min <= 0:
        key = event_key(event_id, event_time, "start")
        if not already_sent(key):
            extra = f"\n\n{details}" if details else ""
            post_embed(
                f"{emoji} {event_name} — ¡COMENZÓ!",
                f"**Servidor:** {server}\n"
                f"**Hora:** {discord_time(event_time)}"
                f"{extra}\n\n"
                f"🔥 ¡Entren ahora!"
            )
            mark_sent(key)


if enabled.get("spacetime_rift", True):
    for dt in candidates_daily(RIFT_HOURS):
        maybe_notify(
            "rift",
            "Spacetime Rift",
            "🌀",
            dt,
            "Los Rifts aparecen 8 veces al día, cada 3 horas."
        )

if enabled.get("beritra_air_raid", True):
    for dt in candidates_hourly(30):
        maybe_notify(
            "beritra",
            "Beritra Air Raid",
            "🐉",
            dt,
            "Beritra aparece cada hora, a los :30."
        )

if enabled.get("abyss_rift_zone", True):
    for dt in candidates_weekly(ABYSS_RIFT_WEEKDAYS, ABYSS_HOUR):
        maybe_notify(
            "abyss_rift",
            "Abyss Rift Zone",
            "⚔️",
            dt,
            "PvP de Elyos vs. Asmodian. Programado martes y jueves a las 22:00 del servidor."
        )

if enabled.get("abyss_event", True):
    for dt in candidates_weekly(ABYSS_EVENT_WEEKDAYS, ABYSS_HOUR):
        maybe_notify(
            "abyss_event",
            "Abyss Event",
            "🔴",
            dt,
            "El tracker de AION2Hub lo lista los miércoles y sábados."
        )

if enabled.get("hourly_minigames", False):
    # AION2Hub lists these recurring events hourly on server time.
    for dt in candidates_hourly(0):
        names = "\n".join(f"• {x}" for x in HOURLY_MINIGAMES)
        maybe_notify(
            "minigames",
            "Eventos y Minijuegos",
            "🎮",
            dt,
            f"Eventos horarios:\n{names}"
        )

# Prune state older than 14 days.
cutoff = now_utc - timedelta(days=14)
cleaned = {}
for key, iso in state.get("sent", {}).items():
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if dt >= cutoff:
            cleaned[key] = iso
    except Exception:
        pass

state["sent"] = cleaned
with STATE_PATH.open("w", encoding="utf-8") as f:
    json.dump(state, f, indent=2)
