# AION 2 → Discord Event Notifications

Ready-to-use GitHub Actions notifier for AION 2 events.

## Default notifications

- 🌀 Spacetime Rift
- 🐉 Beritra Air Raid
- 🔴 Abyss Event
- ⚔️ Abyss Rift Zone
- 15-minute warning
- 5-minute warning
- Event-start notification
- Optional Discord role ping
- TW / KR server selection
- Duplicate protection using `state.json`
- Optional hourly minigames (disabled by default)
- Discord timestamps automatically display in each member's local timezone

## 1. Create your Discord webhook

In Discord:

**Server Settings → Integrations → Webhooks → New Webhook**

Pick the destination channel and copy the webhook URL.

Do not paste the webhook into any public file.

## 2. Upload these files to GitHub

Create a GitHub repository and upload the contents of this folder, including:

- `event_bot.py`
- `config.json`
- `state.json`
- `.github/workflows/events.yml`

## 3. Add the secret

GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

Name:

`DISCORD_WEBHOOK`

Value:

Your full Discord webhook URL.

## 4. Configure the server

Edit `config.json`.

Taiwan:

```json
"server": "TW"
```

Korea:

```json
"server": "KR"
```

## 5. Optional role mention

Enable Developer Mode in Discord, right-click the role you want notified, then **Copy Role ID**.

Put the number in `config.json`:

```json
"role_id": "123456789012345678"
```

Leave it empty to disable role pings:

```json
"role_id": ""
```

The webhook/bot role must be allowed to mention that role in the destination channel.

## 6. Change warnings

Default:

```json
"warning_minutes": [15, 5],
"notify_at_start": true
```

For only a 15-minute warning:

```json
"warning_minutes": [15],
"notify_at_start": false
```

## 7. Hourly minigames

Disabled by default to prevent spam.

To enable:

```json
"hourly_minigames": true
```

## Event schedule used

The script follows the current schedule published/tracked by AION2Hub:

- Spacetime Rift: 02:00 / 05:00 / 08:00 / 11:00 / 14:00 / 17:00 / 20:00 / 23:00 server time
- Beritra Air Raid: every hour at :30
- Abyss Rift Zone: Tuesday and Thursday at 22:00 server time
- Abyss Event: Wednesday and Saturday (configured at 22:00 server time)
- Standard field events/minigames: hourly

TW uses Asia/Taipei (GMT+8).
KR uses Asia/Seoul (GMT+9).

## Testing

After adding `DISCORD_WEBHOOK`, go to:

**GitHub → Actions → AION 2 Event Notifications → Run workflow**

The normal workflow only sends a message when an event is within a configured warning/start window.

For a quick webhook-only test on your own computer, you can temporarily change a scheduled event time in the script or use a test webhook request.

## Important

This project uses the event schedule; it does not continuously scrape AION2Hub. If AION 2 changes an event schedule in a future patch, update the values in `event_bot.py`.

AION2Hub:
https://aion2hub.com/tools/event-timer
