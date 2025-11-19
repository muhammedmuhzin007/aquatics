# Smoke Test Tools

This file documents the local smoke-test harness and how to run it with the mock or Razorpay provider.

- Script: `tools/smoke_check.py`
- Purpose: Create a user, build a small cart, create a draft order, then call the configured payment-provider create/verify endpoints to exercise the end-to-end flow in a lightweight way.

Providers
- `mock` — local, no external network calls. Useful for CI or offline testing.
- `razorpay` — exercise the Razorpay-backed create/verify endpoints. Requires Razorpay test keys and the `razorpay` package to be installed.

Environment / Secrets
- Do NOT commit real secrets to the repo. Prefer to store keys in a local `.env` file listed in `.gitignore` or export them in your shell.
- Keys used for Razorpay (examples):
  - `RAZORPAY_KEY_ID` — your Razorpay key id (test key)
  - `RAZORPAY_KEY_SECRET` — your Razorpay key secret (test key)
  - `RAZORPAY_WEBHOOK_SECRET` — (optional) webhook signing secret to validate incoming webhooks if you test webhooks locally
  - `PAYMENT_PROVIDER` — set to `mock` or `razorpay` (defaults to `razorpay` if not set in settings)

Installing dependencies (optional)
- If you plan to run Razorpay-backed smoke tests, install the Razorpay package into your environment:

```powershell
pip install razorpay
```

Running the smoke test
- Run the harness with the mock provider (no external network calls):

```powershell
python tools/smoke_check.py --provider mock
```

- Run the harness using Razorpay (ensure `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` are set in env or `.env`):

```powershell
$env:RAZORPAY_KEY_ID="rzp_test_..."; $env:RAZORPAY_KEY_SECRET="..."; python tools/smoke_check.py --provider razorpay
```

Notes
- The harness will attempt to create a test user and cart items in your local database. Use this on a development DB only.
 - If you want to test webhook handling, you can either run a public tunnel (ngrok) and configure Razorpay to send webhooks there, or set `RAZORPAY_WEBHOOK_SECRET` to the secret for signature verification and post test webhook payloads manually.
 - If you see failures when running with `--provider razorpay`, confirm your Razorpay keys are correct and that the `razorpay` package is installed.

Troubleshooting
- Run `python manage.py check` to ensure Django system checks pass before running the smoke test.
- If the smoke script fails due to missing migrations/models, run `python manage.py migrate` first.

If you'd like, I can also add a small example `.env.example` file listing the required env vars (without real keys).