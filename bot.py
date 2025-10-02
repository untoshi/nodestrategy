import discord
from discord.ext import commands, tasks
import aiohttp
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Config
API_BASE_URL = os.getenv('API_BASE_URL', 'https://node.auction/api')
UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', 60))

# State tracking
last_status = {}
tracking_channel = None
api_was_down = False

# Color scheme: Orange & Black
ORANGE = 0xFF6B00


def create_status_embed(data):
    """Create clean minimal status embed"""
    
    # Calculate progress
    progress = data['progress_confirmed'] * 100
    progress_bar_length = 20
    filled = int(progress_bar_length * data['progress_confirmed'])
    bar = '█' * filled + '░' * (progress_bar_length - filled)
    
    # Calculate blocks until next price change
    blocks_until_next = data['startHeight'] - data['currentHeight']
    time_estimate_mins = blocks_until_next * 10
    time_estimate_hours = time_estimate_mins / 60
    
    btc_raised = float(data['F_confirmed_BTC'])
    btc_target = data['marketCapBtcSale']
    current_price = data.get('tokenUsdPrice', 0)
    
    # Clean simple embed
    embed = discord.Embed(
        title="NodeStrategy Auction",
        color=ORANGE,
        timestamp=datetime.fromisoformat(data['serverTimeIso'].replace('Z', '+00:00'))
    )
    
    embed.add_field(
        name="Progress",
        value=f"```{progress:.1f}% [{bar}]```",
        inline=False
    )
    
    embed.add_field(
        name="Raised",
        value=f"```{btc_raised:.2f} / {btc_target:.2f} BTC```",
        inline=False
    )
    
    embed.add_field(
        name="Token Price",
        value=f"```${current_price:.6f}```",
        inline=True
    )
    
    if blocks_until_next > 0:
        embed.add_field(
            name="Next Drop",
            value=f"```~{time_estimate_hours:.1f}h```",
            inline=True
        )
    
    embed.set_footer(text="nodestrategy.app")
    
    return embed


async def fetch_status():
    """Fetch auction status from API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{API_BASE_URL}/status', timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json(), resp.status
                return None, resp.status
    except Exception as e:
        print(f'[ERROR] API request failed: {e}')
        return None, 0


@bot.event
async def on_ready():
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="NodeStrategy Auction | !help"
        )
    )
    print(f'[ONLINE] {bot.user.name} connected')
    print(f'[INFO] Bot ready - use !s or !status for auction info')
    print(f'[INFO] Use !track to enable auto-updates in a channel')


@tasks.loop(seconds=UPDATE_INTERVAL)
async def auction_tracker():
    """Main tracking loop"""
    global last_status, tracking_channel, api_was_down
    
    if not tracking_channel:
        return
    
    try:
        data, status_code = await fetch_status()
        
        # Handle API failure - fail silently, don't spam users
        if not data:
            if not api_was_down:
                print(f'[ERROR] API is down (status: {status_code})')
                api_was_down = True
            else:
                print(f'[ERROR] API still down (status: {status_code})')
            return
        
        # API is back up - reset flag silently
        if api_was_down:
            print('[INFO] API is back online')
            api_was_down = False
        
        # Check for alerts
        if last_status:
            # Price drop alert
            if data['T_now'] != last_status.get('T_now'):
                print(f'[ALERT] Price drop detected: ${data.get("tokenUsdPrice", 0):.6f}')
                alert_embed = discord.Embed(
                    title="Price Drop",
                    description=f"New price: ${data.get('tokenUsdPrice', 0):.6f}",
                    color=ORANGE
                )
                try:
                    await tracking_channel.send(embed=alert_embed)
                    print(f'[ALERT] Price drop alert sent')
                except Exception as e:
                    print(f'[ERROR] Failed to send price drop alert: {e}')
            
            # 5% increment milestone alerts
            old_progress = last_status.get('progress_confirmed', 0) * 100
            new_progress = data['progress_confirmed'] * 100
            
            print(f'[DEBUG] Checking milestones: {old_progress:.2f}% → {new_progress:.2f}%')
            
            # Check every 5% milestone
            for milestone in range(5, 101, 5):
                if old_progress < milestone <= new_progress:
                    print(f'[ALERT] Milestone {milestone}% reached!')
                    alert_embed = discord.Embed(
                        title=f"{milestone}% Sold",
                        description=f"{data['F_confirmed_BTC']} BTC raised",
                        color=ORANGE
                    )
                    try:
                        await tracking_channel.send(embed=alert_embed)
                        print(f'[ALERT] Milestone {milestone}% alert sent successfully')
                    except Exception as e:
                        print(f'[ERROR] Failed to send milestone alert: {e}')
        
        last_status = data
        print(f'[UPDATE] Progress: {data["progress_confirmed"]*100:.2f}% | Raised: {data["F_confirmed_BTC"]} BTC')
        
    except Exception as e:
        print(f'[ERROR] Unexpected error in tracker: {e}')


@bot.command(name='status', aliases=['s'])
async def auction_status(ctx):
    """Show current auction status"""
    data, status_code = await fetch_status()
    if data:
        embed = create_status_embed(data)
        await ctx.send(embed=embed)
    else:
        error_embed = discord.Embed(
            title="⚠️ Unable to Fetch Auction Data",
            description=f"The API is currently unavailable (status: {status_code}).\n\nPlease check the live auction at:\n🔗 https://node.auction/",
            color=0xFF0000
        )
        await ctx.send(embed=error_embed)


@bot.command(name='track')
async def start_tracking(ctx):
    """Enable auto-updates in this channel"""
    global tracking_channel
    
    tracking_channel = ctx.channel
    
    if not auction_tracker.is_running():
        auction_tracker.start()
    
    embed = discord.Embed(
        title="Tracking Enabled",
        description=f"Auto-updates will be posted in this channel.\nAlerts every 5% and on price drops.",
        color=ORANGE
    )
    await ctx.send(embed=embed)
    print(f'[INFO] Tracking enabled in #{ctx.channel.name}')


@bot.command(name='stop')
async def stop_tracking(ctx):
    """Disable auto-updates"""
    global tracking_channel
    
    tracking_channel = None
    
    embed = discord.Embed(
        title="Tracking Disabled",
        description="Auto-updates stopped. Use !track to re-enable.",
        color=ORANGE
    )
    await ctx.send(embed=embed)
    print(f'[INFO] Tracking disabled')


@bot.command(name='help', aliases=['h', 'commands'])
async def help_command(ctx):
    """Show available commands"""
    embed = discord.Embed(
        title="NodeStrategy Bot Commands",
        description="Track the NodeStrategy auction in real-time",
        color=ORANGE
    )
    
    embed.add_field(
        name="!s or !status",
        value="Show current auction status",
        inline=False
    )
    
    embed.add_field(
        name="!track",
        value="Enable auto-updates in this channel\nAlerts every 5% and on price drops",
        inline=False
    )
    
    embed.add_field(
        name="!stop",
        value="Disable auto-updates",
        inline=False
    )
    
    embed.add_field(
        name="!help",
        value="Show this help message",
        inline=False
    )
    
    embed.set_footer(text="nodestrategy.app")
    await ctx.send(embed=embed)


if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_TOKEN'))
