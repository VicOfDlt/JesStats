import discord
from discord.ext import commands
from discord.ext.commands.errors import ChannelNotFound
from discord_components.component import Select, SelectOption
from discord_components.interaction import Interaction
from motor.motor_tornado import MotorCursor
from bot import get_embed
from config import db

news = db["news"]


class News(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user.name}: The news extension was loaded successfully.")

    @commands.command(
        name="subscribe",
        aliases=["subscription", "suscribir", "suscribirse", "suscripcion", "sub"],
        description="Use this command to subscribe to one of our news feeds.",
        usage="Usage: `{prefixcommand}` `channel` `news feed`. Do just `{prefixcommand}` for a more detailed way of using this command.",
    )
    async def subscribe(self, ctx, channel: discord.TextChannel = None):
        options = []
        async for f in news.find():
            options.append(
                SelectOption(label=f["_id"], emoji=f["emoji"], value=f["_id"])
            )
        select = [
            Select(
                options=options,
                custom_id="news_select",
                placeholder="Feeds",
                max_values=len(options),
            )
        ]
        if not channel or not isinstance(channel, discord.TextChannel):
            await ctx.send(
                "Which channel would you like me to send the news to? Send the #channel below."
            )

            async def check(m: discord.Message):
                return await commands.TextChannelConverter().convert(ctx, m.content)

            try:
                m: discord.Message = await self.bot.wait_for(
                    "message", timeout=30, check=check
                )
            except TimeoutError:
                await ctx.send("A channel wasn't sent. Timed out.")
            if m:
                channel = await commands.TextChannelConverter().convert(ctx, m.content)
                msg = await ctx.send(
                    "Choose the feeds that you would like to subscribe to below:",
                    components=select,
                )
        elif isinstance(channel, discord.TextChannel):
            msg = await ctx.send(
                "Choose the feeds that you would like to subscribe to below:",
                components=select,
            )

        def check_2(i: Interaction):
            return (
                i.message.id == msg.id
                and i.custom_id == "news_select"
                and i.author == ctx.author
            )

        try:
            i: Interaction = await self.bot.wait_for(
                "select_option", timeout=50, check=check_2
            )
        except TimeoutError:
            await ctx.send("No feeds were selected. Timed out.")
        await msg.edit(components=[])
        feeds = []
        for value in i.values:
            feed = await news.find_one({"_id": value})
            display = []
            feeds.append(value)
            for a in feeds:
                if feeds.index(a) < (len(feeds) - 1):
                    listitem = a + ", "
                else:
                    listitem = "and " + a + "."
                display.append(listitem)
            await news.update_one(feed, {"$push": {"channels": channel.id}})
        await i.respond(
            content=f"You have subscribed correctly for the following feeds in {channel.mention}: {''.join(display)}"
        )
        embed = await get_embed(
            ctx,
            description=f"📰 This channel is now subscribed to the following news feeds: {''.join(display)}",
        )
        await channel.send(embed=embed)

    @commands.command(
        aliases=["subscripciones", "subs"],
        usage="Usage: `{prefixcommand}` `(channel)`. Leave `channel` empty to view subscriptions for all channels.",
        description="Use this command to check which feeds is a channel in the server subscribed to.",
    )
    async def subscribed(
        self, ctx: commands.Context, channel: discord.TextChannel = None
    ):
        embed = await get_embed(ctx, "Subscriptions")
        if not channel or not isinstance(channel, discord.TextChannel):
            async for f in news.find():
                li = []
                for c in ctx.guild.channels:
                    if not isinstance(c, discord.TextChannel):
                        continue
                    if c.id in f["channels"]:
                        li.append(c.name)
                if li:
                    embed.add_field(name=f["_id"], value="\n".join(li), inline=False)

        else:
            channel = await commands.TextChannelConverter().convert(ctx, str(channel))
            li = []
            async for f in news.find():
                if channel.id in f["channels"]:
                    li.append(f["_id"])
            embed.add_field(name=channel.name, value="\n".join(li))
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == self.bot.user.id:
            return


def setup(bot):
    bot.add_cog(News(bot))
