import discord
from discord.ext import commands
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
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{API_BASE_URL}/status') as resp:
            if resp.status == 200:
                return await resp.json()
            return None


@bot.event
async def on_ready():
    print(f'[ONLINE] {bot.user.name} connected')
    print(f'[INFO] Bot ready - use !s or !status for auction info')


@bot.command(name='status', aliases=['s'])
async def auction_status(ctx):
    """Show current auction status"""
    data = await fetch_status()
    if data:
        embed = create_status_embed(data)
        await ctx.send(embed=embed)
    else:
        await ctx.send('Failed to fetch auction data')


if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_TOKEN'))
