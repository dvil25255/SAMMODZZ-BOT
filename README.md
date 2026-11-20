# SAMMODZZ V13 ULTIMATE

Private Telegram bot for secure Lua/TXT file storage, retrieval, metadata, activity logs and license-key generation.

## 1. Requirements

- Python 3.10+
- Telegram bot token from BotFather
- Supabase project
- Your Telegram numeric user ID

## 2. Supabase setup

1. Create a Supabase project.
2. Open SQL Editor.
3. Run `supabase_schema.sql`.
4. Open Project Settings > API.
5. Copy Project URL and the `service_role` secret.
6. Keep the service-role key private. Never share it or embed it in Lua files.

The bot stores file bytes on its host (Termux/VPS) and stores metadata and activity in Supabase. Supabase is not used as a file-byte bucket in this version.

## 3. Configure

Copy `.env.example` to `.env` and fill in:

- `BOT_TOKEN`
- `ADMIN_ID`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

Never commit `.env` to GitHub.

## 4. Termux installation

```bash
pkg update && pkg upgrade -y
pkg install python git -y
termux-setup-storage
mkdir -p ~/SAMMODZZ_V13
```

Extract/copy this project into `~/SAMMODZZ_V13`, then:

```bash
cd ~/SAMMODZZ_V13
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
nano .env
python bot.py
```

For Termux storage in shared memory, set `STORAGE_DIR=/storage/emulated/0/SAMMODZZ_V13/storage` in `.env` after creating that folder. Internal app storage is generally more reliable for databases/logs; shared storage is useful for file access.

## 5. VPS installation

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip unzip
unzip SAMMODZZ_V13.zip
cd SAMMODZZ_V13
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
python bot.py
```

For 24/7 operation, use a process manager such as systemd. Example service file:

```ini
[Unit]
Description=SAMMODZZ V13 Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/SAMMODZZ_V13
ExecStart=/opt/SAMMODZZ_V13/.venv/bin/python /opt/SAMMODZZ_V13/bot.py
Restart=always
RestartSec=5
User=ubuntu

[Install]
WantedBy=multi-user.target
```

Save as `/etc/systemd/system/sammodzz.service`, then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sammodzz
sudo systemctl status sammodzz
journalctl -u sammodzz -f
```

Adjust paths and `User` for your VPS account. Secure `.env` permissions with `chmod 600 .env`.

## 6. Commands

- `/start` - menu
- `/commands` - command list
- `/files` - list stored files
- `/stats` - counts
- `/health` - runtime/storage health
- `/genkey` - generate an application license key
- `/cleanup` - remove backups older than configured retention

Send `.lua` and `.txt` documents to the bot to upload. Files are returned from the Files menu.

## 7. Testing checklist

1. Start the bot and send `/start` from the configured admin account.
2. Send `/start` from another Telegram account. It should say Access denied.
3. Upload a small `.lua` file. Confirm a metadata row appears in `bot_files`.
4. Open Files and download the file. Compare SHA-256 locally.
5. Upload a `.pdf` or `.exe`. It should be rejected.
6. Try a filename containing `../`. It should be sanitized and remain inside storage.
7. Generate a key using `/genkey`. The key hash should appear in `bot_licenses`.
8. Check `/stats` and `/health`.
9. Restart the process and confirm the bot reconnects.

## 8. Operational notes and limitations

- This version uses one admin ID and long polling. Run only one bot process per token.
- Supabase stores metadata and logs; file contents remain on the host filesystem.
- Backups are local copies, not offsite backups. Back up the `storage` folder separately.
- License keys are generated and hashed in Supabase. A consuming app must call a trusted server-side validation endpoint; do not expose the service-role key in client code.
- The current bot generates keys but does not expose a public license-validation API.
- Telegram file download limits and bot API constraints may change. Keep the configured maximum conservative.
- Android may stop background processes. For dependable 24/7 uptime, deploy on a VPS.
