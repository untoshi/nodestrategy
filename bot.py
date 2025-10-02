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

# Auction parameters
AUCTION_ADDRESS = 'bc1pnskr7fwv3kggav9hercy0f2x7zqyndcmjuuvkadyjpm7laxdfh9q09md6k'
TARGET_BTC = 41.58
BLOCKS_PER_DROP = 3

# State tracking
last_status = {}
tracking_channel = None
last_price = None

# Color scheme: Orange & Black
ORANGE = 0xFF6B00


async def fetch_onchain_data():
    """Fetch on-chain data from mempool.space - 100% reliable"""
    try:
        async with aiohttp.ClientSession() as session:
            # Fetch address data
            async with session.get(
                f'https://mempool.space/api/address/{AUCTION_ADDRESS}',
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    return None
                address_data = await resp.json()
            
            # Fetch current block height
            async with session.get(
                'https://mempool.space/api/blocks/tip/height',
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    return None
                block_height = int(await resp.text())
            
            # Fetch BTC price
            async with session.get(
                'https://mempool.space/api/v1/prices',
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    return None
                prices = await resp.json()
                btc_price = prices['USD']
            
            # Calculate progress
            btc_raised = address_data['chain_stats']['funded_txo_sum'] / 100_000_000
            progress = btc_raised / TARGET_BTC
            contribution_count = address_data['chain_stats']['tx_count']
            
            return {
                'btc_raised': btc_raised,
                'progress': progress,
                'contribution_count': contribution_count,
                'current_block': block_height,
                'btc_price': btc_price,
                'source': 'onchain'
            }
    except Exception as e:
        print(f'[ERROR] On-chain data fetch failed: {e}')
        return None


async def fetch_token_price():
    """Try to fetch token price from API - optional"""
    global last_price
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{API_BASE_URL}/status',
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    price = data.get('tokenUsdPrice')
                    if price:
                        last_price = price
                    return price
                return None
    except Exception:
        return None


def create_status_embed(data, token_price=None):
    """Create clean minimal status embed"""
    
    # Calculate progress
    progress = data['progress'] * 100
    progress_bar_length = 20
    filled = int(progress_bar_length * data['progress'])
    bar = '█' * filled + '░' * (progress_bar_length - filled)
    
    # Calculate blocks until next price drop
    blocks_until_next = BLOCKS_PER_DROP - (data['current_block'] % BLOCKS_PER_DROP)
    time_estimate_mins = blocks_until_next * 10
    
    btc_raised = data['btc_raised']
    
    # Clean simple embed
    embed = discord.Embed(
        title="NodeStrategy Auction",
        color=ORANGE,
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(
        name="Progress",
        value=f"```{progress:.1f}% [{bar}]```",
        inline=False
    )
    
    embed.add_field(
        name="Raised",
        value=f"```{btc_raised:.2f} / {TARGET_BTC:.2f} BTC```",
        inline=False
    )
    
    # Show token price if available
    if token_price:
        embed.add_field(
            name="Token Price",
            value=f"```${token_price:.6f}```",
            inline=True
        )
    elif last_price:
        embed.add_field(
            name="Token Price",
            value=f"```${last_price:.6f} (cached)```",
            inline=True
        )
    else:
        embed.add_field(
            name="Token Price",
            value="```Unavailable```",
            inline=True
        )
    
    embed.add_field(
        name="Next Drop",
        value=f"```{blocks_until_next} blocks (~{time_estimate_mins}m)```",
        inline=True
    )
    
    # Add data source footer
    footer_text = "On-chain data via mempool.space"
    if data.get('contribution_count'):
        footer_text = f"{data['contribution_count']} contributions • {footer_text}"
    
    embed.set_footer(text=footer_text)
    
    return embed


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
    """Main tracking loop - uses on-chain data"""
    global last_status, tracking_channel
    
    if not tracking_channel:
        return
    
    try:
        # Fetch on-chain data (reliable)
        data = await fetch_onchain_data()
        
        if not data:
            print('[ERROR] Failed to fetch on-chain data')
            return
        
        # Try to get token price (optional)
        token_price = await fetch_token_price()
        
        # Check for alerts
        if last_status:
            # 5% increment milestone alerts
            old_progress = last_status.get('progress', 0) * 100
            new_progress = data['progress'] * 100
            
            print(f'[DEBUG] Checking milestones: {old_progress:.2f}% → {new_progress:.2f}%')
            
            # Check every 5% milestone
            for milestone in range(5, 101, 5):
                if old_progress < milestone <= new_progress:
                    print(f'[ALERT] Milestone {milestone}% reached!')
                    alert_embed = discord.Embed(
                        title=f"🎯 {milestone}% Sold",
                        description=f"**{data['btc_raised']:.2f} BTC raised**\n{data['contribution_count']} contributions",
                        color=ORANGE
                    )
                    try:
                        await tracking_channel.send(embed=alert_embed)
                        print(f'[ALERT] Milestone {milestone}% alert sent successfully')
                    except Exception as e:
                        print(f'[ERROR] Failed to send milestone alert: {e}')
            
            # Price drop alert (if we have price data)
            if token_price and last_status.get('token_price'):
                # Alert if price dropped significantly (>1%)
                price_change = ((token_price - last_status['token_price']) / last_status['token_price']) * 100
                if price_change < -1:
                    print(f'[ALERT] Price drop detected: ${token_price:.6f} ({price_change:.1f}%)')
                    alert_embed = discord.Embed(
                        title="💰 Price Update",
                        description=f"New price: **${token_price:.6f}**\n({price_change:+.1f}%)",
                        color=ORANGE
                    )
                    try:
                        await tracking_channel.send(embed=alert_embed)
                        print(f'[ALERT] Price drop alert sent')
                    except Exception as e:
                        print(f'[ERROR] Failed to send price drop alert: {e}')
        
        # Store current status
        last_status = data.copy()
        if token_price:
            last_status['token_price'] = token_price
        
        print(f'[UPDATE] Progress: {data["progress"]*100:.2f}% | Raised: {data["btc_raised"]:.2f} BTC | Block: {data["current_block"]}')
        
    except Exception as e:
        print(f'[ERROR] Unexpected error in tracker: {e}')


@bot.command(name='status', aliases=['s'])
async def auction_status(ctx):
    """Show current auction status - uses on-chain data"""
    # Fetch on-chain data
    data = await fetch_onchain_data()
    
    if not data:
        error_embed = discord.Embed(
            title="⚠️ Unable to Fetch Data",
            description="Failed to fetch on-chain data. Please try again in a moment.\n\n🔗 https://node.auction/",
            color=0xFF0000
        )
        await ctx.send(embed=error_embed)
        return
    
    # Try to get token price (optional)
    token_price = await fetch_token_price()
    
    # Create and send embed
    embed = create_status_embed(data, token_price)
    await ctx.send(embed=embed)


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
        description="Track the NodeStrategy auction with real-time on-chain data",
        color=ORANGE
    )
    
    embed.add_field(
        name="!s or !status",
        value="Show current auction status (on-chain data)",
        inline=False
    )
    
    embed.add_field(
        name="!track",
        value="Enable auto-updates in this channel\n• Alerts every 5% milestone\n• Price drop notifications",
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
    
    embed.set_footer(text="Data from Bitcoin blockchain via mempool.space")
    await ctx.send(embed=embed)


if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_TOKEN'))
