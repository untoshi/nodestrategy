# NodeStrategy Auction Bot

Discord bot for tracking the NodeStrategy Dutch auction in real-time.

## Features

- Live auction status updates (every 60s)
- Price drop alerts
- Milestone notifications (25%, 50%, 75%, 100%)
- Terminal-style orange & black aesthetic
- Commands: !auction, !price, !progress, !countdown

## Bot Invite Link

**[Click here to invite the bot](https://discord.com/api/oauth2/authorize?client_id=1423181163383488553&permissions=274877910016&scope=bot)**

Required permissions:
- Send Messages
- Embed Links
- Read Message History
- Use Slash Commands

## Setup

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file with your Discord credentials (already included)

3. Run the bot:
```bash
python bot.py
```

### Deploy to Render

1. Push this repo to GitHub
2. Connect to Render
3. Create a new "Worker" service
4. Set environment variables:
   - `DISCORD_TOKEN`
   - `DISCORD_APPLICATION_ID`
   - `DISCORD_PUBLIC_KEY`

Or use the included `render.yaml` for automatic deployment.

## Commands

- `!auction` - Show current auction status
- `!price` - Display current token price
- `!progress` - Show auction progress bar
- `!countdown` - Time until next price drop
- `!help` - Show available commands

## API Endpoints Used

- `https://node.auction/api/status` - Main auction status
- `https://node.auction/api/transactions` - Transaction history (optional)

## Configuration

Edit `.env` to change:
- `UPDATE_INTERVAL` - Seconds between status updates (default: 60)
- `API_BASE_URL` - NodeStrategy API base URL

## Support

For issues or questions, check https://nodestrategy.app
