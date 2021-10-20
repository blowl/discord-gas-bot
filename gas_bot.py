"""
Run a Discord bot that takes the !gas command and shows the status in an embed + shows the prices in the sidebar
"""
# Example:
# python3 gas_bot.py -s etherscan

from typing import Tuple
from discord.utils import get
import logging
import yaml
import discord
import asyncio
from discord.ext.commands import Bot
import argparse
import requests
import time
import sqlite3
conn = sqlite3.connect("my_database.db")

def database_request(key: str, type: str):
    cursor = conn.cursor()
    if(type=="above"):
        sql = "SELECT * FROM "+type+" WHERE value<"+key
    elif(type=="below"):
        sql = "SELECT * FROM "+type+" WHERE value>"+key  
    cursor.execute(sql)
    rows = cursor.fetchall()
    return rows

def database_delete(key: str, type: str):
    cursor = conn.cursor()
    if(type=="above"):
        sql = "DELETE FROM "+type+" WHERE user="+key
    elif(type=="below"):
        sql = "DELETE FROM "+type+" WHERE user="+key  
    cursor.execute(sql)
    conn.commit()

def insert_database(key: str, value: str, type: str):
    cursor = conn.cursor()
    if(type=="above"):
        sql = "INSERT or replace INTO "+type+" ('user', 'value') VALUES ('"+key+"', '"+value+"')"
    elif(type=="below"):
        sql = "INSERT or replace INTO "+type+" ('user', 'value') VALUES ('"+key+"', '"+value+"')" 
    cursor.execute(sql)
    conn.commit()

def get_gas_from_etherscan(key: str,
                           verbose: bool = False) -> Tuple[int, int, int]:
    """
    Fetch gas from Etherscan API
    """
    r = requests.get('https://api.etherscan.io/api',
                     params={'module': 'gastracker',
                             'action': 'gasoracle',
                             'apikey': key})
    if r.status_code == 200:
        if verbose:
            print('200 OK')
        data = r.json().get('result')
        return int(data['FastGasPrice']), int(data['ProposeGasPrice']), int(data['SafeGasPrice'])
    else:
        if verbose:
            print(r.status_code)
        time.sleep(10)


def get_gas_from_ethgasstation(key: str, verbose: bool = False):
    """
    Fetch gas from ETHGASSTATION API
    """
    r = requests.get('https://ethgasstation.info/api/ethgasAPI.json?', params={'api-key': key})
    if r.status_code == 200:
        if verbose:
            print('200 OK')
        data = r.json()
        return int(data['fastest'] / 10), int(data['fast'] / 10), int(data['average'] / 10), int(
            data['safeLow'] / 10), int(data['fastestWait'] * 60), int(data['fastWait'] * 60), int(
            data['avgWait'] * 60), int(data['safeLowWait'] * 60)
    else:
        if verbose:
            print(r.status_code)
        time.sleep(10)

def main(source, verbose=False):
    # 1. Instantiate the bot
    # Allow the command prefix to be either ! or %
    bot = Bot(command_prefix=('!', '%'), help_command=None)

    @bot.command(pass_context=True, brief="Get ETH gas prices")
    async def gas(ctx):
        embed = discord.Embed(title=":fuelpump: Current gas prices")
        if source == 'ethgasstation':
            fastest, fast, average, slow, fastestWait, fastWait, avgWait, slowWait = get_gas_from_ethgasstation(
                config['ethgasstationKey'],
                verbose=verbose)
            embed.add_field(name=f"Slow :turtle: | {slowWait} seconds", value=f"{round(float(slow), 1)} Gwei",
                            inline=False)
            embed.add_field(name=f"Average :person_walking: | {avgWait} seconds",
                            value=f"{round(float(average), 1)} Gwei", inline=False)
            embed.add_field(name=f"Fast :race_car: | {fastWait} seconds", value=f"{round(float(fast), 1)} Gwei",
                            inline=False)
            embed.add_field(name=f"Quick :zap: | {fastestWait} seconds", value=f"{round(float(fastest), 1)} Gwei",
                            inline=False)
        else:
            if source == 'etherscan':
                fast, average, slow = get_gas_from_etherscan(config['etherscanKey'], verbose=verbose)
            embed.add_field(name=f"Slow :turtle:", value=f"{slow} Gwei", inline=False)
            embed.add_field(name=f"Average :person_walking:", value=f"{average} Gwei", inline=False)
            embed.add_field(name=f"Fast :zap:", value=f"{fast} Gwei", inline=False)
        embed.set_footer(text=f"Fetched from {source}\nUse help to get the list of commands")
        embed.set_author(
            name='{0.display_name}'.format(ctx.author),
            icon_url='{0.avatar_url}'.format(ctx.author)
        )
        await ctx.send(embed=embed)

    @bot.command(pass_context=True, brief="Receive alerts for gas prices via dms")
    async def alert(ctx, arg1, arg2):
        await ctx.send('you passed {} and {}'.format(arg1, arg2)) 
        if(arg1=="above"):
            insert_database(str(ctx.message.author.id), arg2, str(arg1))
        elif(arg1=="below"):
            insert_database(str(ctx.message.author.id), arg2, str(arg1))
        else:
            ctx.send('invalid arguments')

    @bot.command(pass_context=True, brief="Get list of commands")
    async def help(ctx, args=None):
        help_embed = discord.Embed(
            title="Gas Tracker",
            colour=discord.Colour.from_rgb(206, 17, 38))
        help_embed.set_author(
            name='{0.display_name}'.format(ctx.author),
            icon_url='{0.avatar_url}'.format(ctx.author)
        )
        command_list = [x for x in bot.commands if not x.hidden]

        def sortCommands(value):
            return value.name

        command_list.sort(key=sortCommands)
        if not args:
            help_embed.add_field(
                name="Command Prefix",
                value="`!`",
                inline=False)
            help_embed.add_field(
                name="List of supported commands:",
                value="```" + "\n".join(['{:>2}. {:<14}{}'.format(str(i + 1), x.name, x.brief) for i, x in
                                         enumerate(command_list)]) + "```",
                inline=False
            )
        else:
            help_embed.add_field(
                name="Nope.",
                value="Don't think I got that command, boss."
            )

        help_embed.set_footer(text="For any inquiries, suggestions, or bug reports, get in touch with @Nerte#1804")
        await ctx.send(embed=help_embed)

    # 2. Load config
    filename = 'config.yaml'
    with open(filename) as f:
        config = yaml.load(f, Loader=yaml.Loader)

    async def send_update(fastest, average, slow,  rowsabove, rowsbelow, **kw,):
        print('fuck')
        status = f'⚡{fastest} |🐢{slow} | !help'
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing,
                                                            name=status))

        if(len(rowsabove)!=0 or len(rowsbelow)!=0):
            for guild in bot.guilds:
                if(len(rowsabove)!=0):
                    for row in rowsabove:
                        user = await bot.fetch_user(row[0])
                        await user.send('GAS ALERT: GAS IS NOW ABOVE '+str(row[1]))
                        database_delete(row[0], 'above')
                if(len(rowsbelow)!=0):
                    for row in rowsbelow:
                        user = await bot.fetch_user(row[0])
                        await user.send('GAS ALERT: GAS IS NOW BELOW '+str(row[1]))
                        database_delete(row[0], 'below')
                guser = guild.get_member(bot.user.id);
                await guser.edit(nick=f'Gas: 🚶{average}');

        await asyncio.sleep(config['updateFreq'])  # in seconds

    def create_table(conn, create_table_sql):
        c = conn.cursor()
        c.execute(create_table_sql)

    @bot.event
    async def on_ready():
        """
        When discord client is ready
        """
        sql_create_above_table = """ CREATE TABLE IF NOT EXISTS above (
                                    user text PRIMARY KEY,
                                    value integer NOT NULL
                                ); """
        sql_create_below_table = """ CREATE TABLE IF NOT EXISTS below (
                                    user text PRIMARY KEY,
                                    value integer NOT NULL
                                ); """
        create_table(conn, sql_create_above_table)
        create_table(conn, sql_create_below_table)

        while True:
            # 3. Fetch gas
            try:
                if source == 'etherscan':
                    gweiList = get_gas_from_etherscan(config['etherscanKey'],
                                                      verbose=verbose)
                elif source == 'ethgasstation':
                    gweiList = get_gas_from_ethgasstation(config['ethgasstationKey'])
                    rowsabove = database_request(str(gweiList[2]), 'above')
                    rowsbelow = database_request(str(gweiList[2]), 'below')
                    await send_update(gweiList[0], gweiList[2], gweiList[3], rowsabove, rowsbelow)
                    continue
                else:
                    raise NotImplemented('Unsupported source')
                # 4. Feed it to the bot
                await send_update(*gweiList)
            except Exception as exc:
                logger.error(exc)
                continue

    bot.run(config['discordBotKey'])


if __name__ == '__main__':
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

    parser = argparse.ArgumentParser()

    parser.add_argument('-s', '--source',
                        choices=['etherscan', 'ethgasstation'],
                        default='etherscan',
                        help='select API')

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='toggle verbose')
    args = parser.parse_args()
    main(source=args.source,
         verbose=args.verbose)
