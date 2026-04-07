Send a promotional/notification message to VetAI users via Telegram bot.

Use `rtk proxy curl` for the HTTP request. Header: `admin-key: vetai-admin-2026`.

## How to use

Ask the user for:
1. **Message text** — what to send (will be wrapped in HTML, support `<b>`, `<i>`, `<code>`)
2. **Target** — who to send to:
   - `all` — all users (excluding test)
   - `active` — users who made at least 1 request
   - A specific `telegram_id` number

A [Open VetAI] button is automatically appended to every message.

## Endpoint

```
POST https://vetai-backend.azurewebsites.net/api/v1/users/admin/send-message
Header: admin-key: vetai-admin-2026
Content-Type: application/json
Body: {"text": "...", "target": "all" | "active" | 370577745}
```

## Example

```bash
rtk proxy curl -s -X POST \
  -H "admin-key: vetai-admin-2026" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello!", "target": "all"}' \
  "https://vetai-backend.azurewebsites.net/api/v1/users/admin/send-message"
```

## Output

Show the response: sent count, failed count, blocked users list. Confirm with user before sending.
