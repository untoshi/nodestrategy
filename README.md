# 🟠 NodeStrategy Auction Bot

Track the **NodeStrategy Dutch Auction** live in your Discord server. Get real-time alerts for price drops and milestones, or check the status on-demand.

---

## 🚀 Add to Your Server

**[➜ Add Bot to Discord](https://discord.com/api/oauth2/authorize?client_id=1423181163383488553&permissions=277025770496&scope=bot)**

No configuration needed—just click, authorize, and start using!

---

## ✨ Features

- **On-Demand Status** - Check auction progress anytime with `!s`
- **Opt-In Auto-Updates** - Enable live alerts in any channel with `!track`
- **5% Milestone Alerts** - Get notified at 5%, 10%, 15%... up to 100%
- **Price Drop Notifications** - Instant alerts when token price drops
- **Clean Design** - Minimalist orange & black aesthetic
- **Bot Status** - Shows "Watching NodeStrategy Auction | !help" in member list

---

## 📖 Quick Start Guide

### 1️⃣ Invite the Bot
Click the **[Add Bot to Discord](https://discord.com/api/oauth2/authorize?client_id=1423181163383488553&permissions=277025770496&scope=bot)** button above and select your server.

### 2️⃣ Check Auction Status
Type `!s` or `!status` in any channel to see current auction info:
- Progress percentage
- BTC raised
- Token price
- Time to next price drop

### 3️⃣ (Optional) Enable Auto-Updates
Want live alerts? Type `!track` in your desired channel:
- Get alerts every 5% milestone
- Get alerts on price drops
- Only the channel where you ran `!track` will receive updates

### 4️⃣ Stop Updates
To disable auto-updates, type `!stop`

---

## 🎮 Commands

| Command | Description |
|---------|-------------|
| `!s` or `!status` | Show current auction status |
| `!track` | Enable auto-updates in this channel |
| `!stop` | Disable auto-updates |
| `!help` | Show all commands |

**Examples:**
```
!s              → Quick status check
!track          → Start receiving live alerts here
!stop           → Turn off alerts
```

---

## 🔧 Self-Hosting (Optional)

Want to run your own instance? Here's how:

### Local Development

1. **Clone the repo**
   ```bash
   git clone https://github.com/untoshi/nodestrategy-bot.git
   cd nodestrategy-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create `.env` file**
   ```env
   DISCORD_TOKEN=your_bot_token
   DISCORD_APPLICATION_ID=your_app_id
   DISCORD_PUBLIC_KEY=your_public_key
   API_BASE_URL=https://node.auction/api
   UPDATE_INTERVAL=60
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

### Deploy to Render

1. Fork this repo to your GitHub
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click **"New +"** → **"Background Worker"**
4. Connect your GitHub repo
5. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - Add environment variables from `.env`
6. Deploy!

---

## 📊 API Data Source

This bot pulls live data from:
- **[NodeStrategy Auction API](https://node.auction/api/status)** - Real-time auction status
- **[NodeStrategy Website](https://nodestrategy.app)** - Official project site

---

## 🤝 Contributing

Found a bug or have a feature request? Open an issue or submit a PR!

---

## 📜 License

MIT License - Feel free to fork and modify!

---

## 🔗 Links

- **[NodeStrategy Website](https://nodestrategy.app)**
- **[GitHub Repository](https://github.com/untoshi/nodestrategy-bot)**
- **[Add Bot to Discord](https://discord.com/api/oauth2/authorize?client_id=1423181163383488553&permissions=277025770496&scope=bot)**

---

**Built for the Ordinals community** 🟠
