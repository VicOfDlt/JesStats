import discord, requests, os
from discord.ext import commands, tasks
from discord_components import DiscordComponents
from config import token, db
from typing import Union
from help_ import CustomHelpCommand


config = db["config"]
links = db["linked"]

presence_count = 0


async def get_embed(ctx: commands.Context, title=None, description=None, color=None):
    b_config = await config.find_one({"_id": "config"})
    if not color:
        color = b_config["color"]
    kwargs = {"color": color}
    if title:
        kwargs["title"] = title
    if description:
        kwargs["description"] = description
    embed = discord.Embed(**kwargs)
    embed.set_footer(
        text="Made by Vic__dtl and FusedTundra10",
        icon_url=b_config["footer"],
    )
    embed.set_author(
        name=ctx.message.author.display_name, icon_url=ctx.author.avatar.url
    )
    embed.set_thumbnail(url=b_config["thumbnail"])
    return embed


async def is_server_online(ctx):
    res = requests.get("https://jesapi2.herokuapp.com/4")
    active = res.json()["serverOnline"]
    if active:
        return True
    return await ctx.send(
        embed=await get_embed(
            ctx, ":red_circle: The server is offline, can't find that info"
        )
    )


async def find_linked(user: Union[discord.User, int, commands.Context]):
    if isinstance(user, commands.Context):
        id_ = user.message.author.id
    elif isinstance(user, (discord.User, discord.Member)):
        id_ = user.id
    else:
        id_ = user
    players = await links.find_one({"_id": "players"})
    if id_ in players:
        return players["ign"]
    else:
        return


intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="/",
    intents=intents,
    help_command=CustomHelpCommand(),
    case_insensitive=True,
)
DiscordComponents(bot)


@tasks.loop(seconds=20)
async def change_presence():
    global presence_count
    presences = [
        {
            "activity": discord.Activity(
                type=discord.ActivityType.watching, name=f"{len(bot.guilds)} Servers"
            )
        },
        {
            "activity": discord.Activity(
                type=discord.ActivityType.watching, name=f"{len(bot.guilds)} Servers"
            )
        },
        {
            "activity": discord.Activity(
                type=discord.ActivityType.watching, name="ciel0"
            )
        },
    ]
    await bot.change_presence(**presences[presence_count])
    if presence_count == 2:
        presence_count = 0
    else:
        presence_count += 1


@bot.event
async def on_ready():
    print(f"{bot.user.name}: Bot loaded successfully. ID: {bot.user.id}")
    change_presence.start()


if __name__ == "__main__":
    bot.load_extension("cogs.commands")
    bot.load_extension("cogs.news")

    bot.run(token)
