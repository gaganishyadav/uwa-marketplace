# Deployment Guide — Cloudflare Tunnel

Host the UWA Marketplace on your Mac and expose it to the internet via a free Cloudflare Tunnel URL.

## Prerequisites

- Python 3 with your venv activated
- `cloudflared` installed (`brew install cloudflared`)
- Your Mac stays on and awake while demoing

## Step 1: Activate your virtual environment

```bash
cd /Users/sawetr/Documents/uwa-marketplace
source venv/bin/activate
```

## Step 2: Start the Flask app (Terminal 1)

python run.py
```

You should see: `Running on http://127.0.0.1:5000`

## Step 3: Start the Cloudflare Tunnel (Terminal 2)

Open a **second terminal** and run:

```bash
cloudflared tunnel --url http://127.0.0.1:5000 --config /dev/null
```

> The `--config /dev/null` flag is important — it bypasses any existing cloudflared config on your machine that could interfere.

You will see output like:

```
|  https://some-random-words.trycloudflare.com  |
```

That URL is your public link. Send it to anyone to access your site.

## Step 4: Stop the tunnel

Press `Ctrl+C` in **both** terminals when you're done.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Port 5000 already in use | Use port 5001 instead (macOS AirPlay uses 5000) |
| Tunnel returns 404 | Make sure to include `--config /dev/null` to bypass old configs |
| URL not reachable | Wait 10-30 seconds after tunnel starts, it takes a moment to propagate |
| CSRF token missing | This is normal for curl tests — browsers handle it automatically |

## Notes

- The tunnel URL changes every time you restart cloudflared
- No Cloudflare account needed for quick tunnels
- WebSockets (chat) work through Cloudflare Tunnel
- Your other projects using named tunnels are not affected
- All data (SQLite database, uploaded images) is stored on your local machine
