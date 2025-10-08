# Automated Newsletter Generation Setup

## Problem
Your cron job starts containers but doesn't generate newsletters because there's no scheduled task configured.

## Solution
I've added a cron endpoint `/api/cron/generate` that can be called by external cron services.

## Setup Options

### Option 1: Use GitHub Actions (Recommended)
Create `.github/workflows/newsletter-cron.yml`:

```yaml
name: Generate Newsletter
on:
  schedule:
    - cron: '0 9 * * 1-5'  # 9 AM EST, Monday-Friday
  workflow_dispatch:  # Allow manual trigger

jobs:
  generate-newsletter:
    runs-on: ubuntu-latest
    steps:
      - name: Generate Newsletter
        run: |
          curl -X POST \
            -H "X-Cron-Secret: ${{ secrets.CRON_SECRET }}" \
            -H "Content-Type: application/json" \
            https://web-production-c4672.up.railway.app/api/cron/generate
```

### Option 2: Use Railway Cron Service
1. Go to Railway dashboard
2. Add a new service
3. Choose "Cron" template
4. Set schedule: `0 9 * * 1-5` (9 AM EST, Monday-Friday)
5. Set command: `curl -X POST -H "X-Cron-Secret: $CRON_SECRET" https://web-production-c4672.up.railway.app/api/cron/generate`

### Option 3: Use External Cron Service
Services like:
- **cron-job.org** - Free web-based cron
- **EasyCron** - Reliable cron service
- **SetCronJob** - Simple cron service

Set up a POST request to:
- URL: `https://web-production-c4672.up.railway.app/api/cron/generate`
- Headers: `X-Cron-Secret: your-secret-here`
- Schedule: Daily at 9 AM EST

## Environment Variables

Add to your Railway project:
- `CRON_SECRET` - A secret string to secure the cron endpoint

## Testing

Test the cron endpoint manually:
```bash
curl -X POST \
  -H "X-Cron-Secret: your-secret" \
  -H "Content-Type: application/json" \
  https://web-production-c4672.up.railway.app/api/cron/generate
```

## Schedule Examples

- `0 9 * * 1-5` - 9 AM EST, Monday-Friday
- `0 8 * * *` - 8 AM EST, every day
- `0 9 * * 1` - 9 AM EST, every Monday
- `0 9 1 * *` - 9 AM EST, first day of every month

## What This Fixes

✅ **Automated newsletter generation** - Newsletters will be generated automatically
✅ **No manual intervention** - Runs on schedule without human input
✅ **Secure endpoint** - Protected with secret key
✅ **Proper logging** - All cron activities are logged
✅ **Database storage** - Generated newsletters are saved to PostgreSQL
