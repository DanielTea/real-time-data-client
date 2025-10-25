# 🚀 START HERE

## Quick Start (One Command!)

```bash
bash start-all.sh
```

**That's it!** Everything will install and start automatically.

---

## ⚠️ Important Notes

### Run with Bash

Always use `bash` to run the script:

✅ **Correct:**

```bash
bash start-all.sh
./start-all.sh
```

❌ **Wrong:**

```bash
sh start-all.sh  # This won't work!
```

### First Time?

Before running, make sure you have:

1. **Node.js 18+** installed
2. **Python 3.10+** installed
3. **Polymarket credentials** in `keys.env` (run `python generate_api_key.py` first)

---

## What Happens

The script will automatically:

- ✅ Install dependencies (pnpm, uv, Node packages, Python packages)
- ✅ Start WebSocket server (port 8080)
- ✅ Start Trading server (port 5000)
- ✅ Start Frontend (port 5173)
- ✅ Open browser to http://localhost:5173

---

## Stop Everything

```bash
bash stop-all.sh
```

Or press **Ctrl+C**

---

## Troubleshooting

### Script stops after "Installing Python dependencies"

You're probably using `sh` instead of `bash`. Use:

```bash
bash start-all.sh
```

### "Permission denied"

Make the script executable:

```bash
chmod +x start-all.sh stop-all.sh
./start-all.sh
```

### Services not starting

Clean and restart:

```bash
bash stop-all.sh
rm -rf node_modules frontend/node_modules .venv logs
bash start-all.sh
```

---

## Next Steps

1. **View Dashboard**: Automatically opens at http://localhost:5173
2. **Enable Trading** (optional):
    - Get API keys from Alpaca and Claude
    - Configure in Settings → Trading API Configuration
    - Use Trading Chat to trade with AI!

---

## More Info

- Simple guide: [USAGE.md](USAGE.md)
- Quick reference: [QUICK-REFERENCE.md](QUICK-REFERENCE.md)
- Full docs: [README.md](README.md)

---

**Remember: Use `bash start-all.sh` not `sh start-all.sh`** ✅
