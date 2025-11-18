# Smoke Test Tools

This file documents the local smoke-test harness and how to run it with the mock or Stripe provider.

- Script: `tools/smoke_check.py`
- Purpose: Create a user, build a small cart, create a draft order, then call the configured payment-provider create/verify endpoints to exercise the end-to-end flow in a lightweight way.

Providers
- `mock` — local, no external network calls. Useful for CI or offline testing.
- `stripe` — exercise the Stripe-backed create/verify endpoints. Requires Stripe test keys and the `stripe` package to be installed.

Environment / Secrets
- Do NOT commit real secrets to the repo. Prefer to store keys in a local `.env` file listed in `.gitignore` or export them in your shell.
- Keys used for Stripe (examples):
  - `STRIPE_SECRET_KEY` — your Stripe secret key (starts with `sk_test_` in test mode)
  - `STRIPE_PUBLISHABLE_KEY` — your Stripe publishable key (starts with `pk_test_`)
  - `STRIPE_WEBHOOK_SECRET` — (optional) webhook signing secret to validate incoming webhooks if you test webhooks locally
  - `PAYMENT_PROVIDER` — set to `mock` or `stripe` (defaults to `stripe` if not set in settings)

Installing dependencies (optional)
- If you plan to run Stripe-backed smoke tests, install the Stripe package into your environment:

```powershell
pip install stripe
```

Running the smoke test
- Run the harness with the mock provider (no external network calls):

```powershell
python tools/smoke_check.py --provider mock
```

- Run the harness using Stripe (ensure `STRIPE_SECRET_KEY` is set in env or `.env`):

```powershell
$env:STRIPE_SECRET_KEY="sk_test_..."; $env:STRIPE_PUBLISHABLE_KEY="pk_test_..."; python tools/smoke_check.py --provider stripe
```

Notes
- The harness will attempt to create a test user and cart items in your local database. Use this on a development DB only.
- If you want to test webhook handling, you can either run a public tunnel (ngrok) and configure Stripe to send webhooks there, or set `STRIPE_WEBHOOK_SECRET` to the secret for signature verification and post test webhook payloads manually.
- If you see failures when running with `--provider stripe`, confirm your Stripe keys are correct and that the `stripe` package is installed.

Troubleshooting
- Run `python manage.py check` to ensure Django system checks pass before running the smoke test.
- If the smoke script fails due to missing migrations/models, run `python manage.py migrate` first.

If you'd like, I can also add a small example `.env.example` file listing the required env vars (without real keys).