# TeleLedger — Implementation Notes

Scaffold generated from the PRD. Two folders: `backend/` (Django + DRF, deploy to Render)
and `frontend/` (static SPA, deploy to Vercel/GitHub Pages).

## How the pieces map to the PRD

| PRD Section | Implementation |
|---|---|
| 4.1 Telegram Auth | `frontend/js/api.js` sends the raw `Telegram.WebApp.initData` string in the `Authorization: TelegramWebApp <data>` header on every request. `backend/core/auth.py` (`TelegramInitDataAuthentication`) re-derives the HMAC-SHA256 hash per Telegram's spec, rejects tampered or stale (`auth_date` > `TELEGRAM_AUTH_MAX_AGE`) requests, and auto-creates/fetches the matching `Profile` row — this is your `get_or_create` "auto-login." |
| 4.2 Transactions | `Transaction` model + `TransactionViewSet` (full CRUD). `DashboardView` aggregates cash/online/net balances with a single query using Django's `Sum`. |
| 4.3 Collections | `Collection` model + `CollectionViewSet`. The `settle` custom action flips `is_settled` **and** writes a matching `Transaction` row automatically (income if `to_receive`, expense if `to_give`), exactly as specified. |
| 4.4 Reminders | `Reminder` model + `ReminderViewSet` for CRUD. `core/scheduler.py` registers a `django-apscheduler` job (`send_due_reminders`) that runs every 5 minutes, queries `is_sent=False AND remind_at <= now`, and calls the Telegram Bot `sendMessage` API directly (no extra dependency needed). Started automatically in `core/apps.py`'s `ready()`. |
| 5. Schema | Models mirror the tables exactly. Note: the PRD listed `username` as type "Vibrant" (typo) — implemented as `CharField`, nullable, which is what was clearly intended. |
| 6. UI/UX | `frontend/index.html` is capped at `max-w-[430px]` and uses a fixed bottom tab bar with the four PRD tabs. `app.js` does simple client-side routing between them — no framework needed for this scope. |
| 7. Cold-start UX | `app.js`'s `warmUpBackend()` pings `/api/dashboard/` before showing the app, updating the loading text with elapsed seconds so the user understands the Render free-tier delay rather than thinking the app is broken. |
| 7. Cron | Handled via `django-apscheduler` (in-process, no extra infra) rather than an external cron pinger — simpler for a free-tier single Render service, since Render's own web dyno process runs the scheduler thread. If you'd rather decouple this from web traffic, swap it for an external uptime-ping service that hits a `/api/cron/tick/` endpoint every 5 min instead. |

## What you need to fill in before deploying

1. **Environment variables** (Render dashboard): `DJANGO_SECRET_KEY`, `TELEGRAM_BOT_TOKEN`, `SUPABASE_DB_*` (from Supabase → Project Settings → Database).
2. **`frontend/js/api.js`**: update `API_BASE` to your actual Render URL once deployed.
3. **CORS**: `CORS_ALLOW_ALL_ORIGINS = True` is set for quick bring-up — tighten to your real Vercel/GitHub Pages origin before going live.
4. Run `python manage.py makemigrations core && python manage.py migrate` once your Supabase credentials are in place (migrations aren't pre-generated here since they depend on your exact Postgres/Supabase setup).

## Folder structure
```
teleledger/
├── backend/
│   ├── config/          # settings, urls, wsgi
│   ├── core/            # models, auth, views, serializers, scheduler
│   ├── requirements.txt
│   └── Procfile
└── frontend/
    ├── index.html
    ├── css/style.css
    └── js/{api.js, app.js}
```

## Not implemented (out of scope for this pass, flagging explicitly)
- Category/payment-method management UI (edit/delete on collections & reminders — currently create + list + settle only, matching the PRD's "Quick Actions" emphasis).
- Automated tests.
- Rich text rendering for notes (PRD says "Rich Text Notes" but plain text covers the functional need; swap the `<textarea>` for a lightweight editor like Quill if true rich text is required).
