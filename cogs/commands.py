import discord, asyncio, requests
from discord.ext import commands
from discord_components import Interaction, Button, ButtonStyle
from bot import find_linked, get_embed, is_server_online

townapi = requests.get(os.environ['townapi'])
nationapi = requests.get(os.environ['nationapi'])
resapi = requests.get(os.environ['resapi'])
serverapi = requests.get(os.environ['serverapi'])
onlineapi = requests.get(os.environ['onlineapi'])
townlessapi = requests.get(os.environ['townlessapi'])
allplayersapi = requests.get(os.environ['allapi'])
sw = requests.get(os.environ['sw'])


class Temp:
    def __init__(self, ctx: commands.Context, reslist, embed=None, arg2=None):
        self.ctx = ctx
        self.bot: commands.Bot = ctx.bot
        self.list = None
        self.msg: discord.Message = None
        self.page = 1
        self.reslist = reslist
        self.arg2 = arg2
        if embed:
            res_per_page = 10
            self.split_list = [
                reslist[i : i + res_per_page]
                for i in range(0, len(reslist), res_per_page)
            ]
            self.total_pages = len(self.split_list)

    def get_buttons(self):
        components = [[]]

        p_disbled = self.page == 1
        components[0].append(
            Button(
                emoji="⏪",
                style=ButtonStyle.blue,
                custom_id="previous",
                disabled=p_disbled,
            )
        )
        components[0].append(
            Button(
                label=f"{self.page}/{self.total_pages}",
                style=ButtonStyle.blue,
                custom_id="page_count",
                disabled=True,
            )
        )
        n_disbled = self.page == self.total_pages
        components[0].append(
            Button(
                emoji="⏭️", style=ButtonStyle.blue, custom_id="next", disabled=n_disbled
            )
        )

        return components

    async def wait_for_buttons(self):
        def check(i: Interaction):
            return i.author == self.ctx.author and i.message.id == self.msg.id

        try:
            interaction: Interaction = await self.bot.wait_for(
                "button_click", timeout=80, check=check
            )
        except asyncio.TimeoutError:
            return await self.msg.edit(components=[])
        if interaction.custom_id == "next":
            self.page += 1
        else:
            self.page -= 1

        await self.switch_page(interaction)

    async def edit_embed(self):
        embed: discord.Embed = self.msg.embeds[0]
        embed.remove_field(4)
        embed.add_field(
            name="Residents: ",
            value="\n".join(self.split_list[self.page - 1]),
            inline=False,
        )
        return embed

    async def switch_page(self, interaction: Interaction):
        await interaction.edit_origin(
            embed=await self.edit_embed(), components=self.get_buttons()
        )
        await self.wait_for_buttons()

    async def online(self):
        if not self.arg2:
            if not await (player := find_linked(self.ctx.message.author)):
                return await self.ctx.send_help(self.ctx.command)
            resident = requests.get(f"{townapi}/{player}")
            self.arg2 = resident.json()["town"]
        res = requests.get(onlineapi)
        embed = await get_embed(
            self.ctx, title=f"Online Players in {self.arg2.lower()}"
        )
        li = [
            res.json()[i]["name"]
            for i in range(len(res.json()))
            if "town" in res.json()[i]
            and res.json()[i]["town"].lower() == self.arg2.lower()
        ]

        embed.add_field(name="Online: ", value=str(len(li)), inline=False)
        if li:
            embed.add_field(
                name="Names: ", value="```" + "\n".join(li) + "```", inline=False
            )
        await self.reslist.delete()
        await self.ctx.send(embed=embed)


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user.name}: The commands extension was loaded successfully.")

    @commands.command(
        aliases=["town", "towns"],
        description="Use this command to find info about a specific town.",
        usage="Usage: `{prefixcommand}` `(online)` `(town)`.\nDo `{prefixcommand}` `town` to check the town's info.\nDo `{prefixcommand}` `online` `town` to see who's online in that town.\nLeave `town` empty to see your /linked town's info",
    )
    async def t(self, ctx: commands.Context, arg=None, arg2=None):
        if not arg and not await find_linked(ctx.message.author):
            return await ctx.send_help(ctx.command)
        if await is_server_online(ctx) != True:
            return

        wait_msg = await ctx.reply(
            embed=await get_embed(
                ctx=ctx,
                description="<a:happy_red:912452454669508618> Fetching town data ...",
            )
        )

        if arg.lower() == "online":
            temp = Temp(ctx, wait_msg, arg2=arg2)
            return await temp.online()

        if not arg and await (player := find_linked(ctx.message.author)):
            resident = requests.get(f"{townapi}/{player}")
            arg = resident.json()["town"]

        res = requests.get(f"{townapi}/{arg}")
        if res.json() == "That town does not exist!":
            await wait_msg.delete()
            return await ctx.reply(
                embed=await get_embed(
                    ctx,
                    description="<a:crya:912762373591420989> This town doesn't exist...",
                    color=discord.Color.red(),
                )
            )

        embed = await get_embed(ctx, f"Town: {res.json()['name']}")
        embed.add_field(name="Mayor", value=res.json()["mayor"], inline=True)
        embed.add_field(name="Nation", value=res.json()["nation"], inline=True)
        embed.add_field(
            name="Dynmap",
            value=f"[{res.json()['x']},{res.json()['z']}](http://jes.enviromc.com:25568/#/?worldname=earth&mapname=flat&zoom=6&x={res.json()['x']}&y=64&z={res.json()['z']})",
            inline=False,
        )
        embed.add_field(
            name="Claims",
            value=f"{str(res.json()['area'])}/{str(len(res.json()['residents'] * 8))}",
            inline=False,
        )

        reslist: list = res.json()["residents"]
        temp = Temp(ctx, reslist, embed)

        embed.add_field(
            name="Residents: ", value="\n".join(temp.split_list[0]), inline=False
        )
        await wait_msg.delete()
        temp.msg = await ctx.send(embed=embed, components=temp.get_buttons())

        await temp.wait_for_buttons()

    @commands.command(
        aliases=["resident", "residents"],
        usage="Usage: `{prefixcommand}` `(username)`.\nLeave `username` empty to view your /linked resident info.",
        description="Use this commands to get a player's info. Make sure to type the '_' if it's a bedrock player.",
    )
    async def res(self, ctx: commands.Context, arg=None):
        if not arg and not await find_linked(ctx.message.author):
            return await ctx.send_help(ctx.command)
        if await is_server_online(ctx) != True:
            return

        wait_msg = await ctx.reply(
            embed=await get_embed(
                ctx=ctx,
                description="<a:happy_red:912452454669508618> Fetching resident data ...",
            )
        )

        if not arg and await (player := find_linked(ctx.message.author)):
            arg = player
        res = requests.get(f"{resapi}/{arg}")

        embed = await get_embed(ctx, title=f"Resident: {res.json()['name']}")
        embed.add_field(name="Nation: ", value=str(res.json()["nation"]), inline=False)
        embed.add_field(name="Town: ", value=str(res.json()["town"]), inline=False)
        embed.add_field(name="Rank: ", value=str(res.json()["rank"]), inline=False)
        await wait_msg.delete()
        await ctx.send(embed=embed)

    @commands.command(
        aliases=["nation", "nations"],
        usage="Usage: `{prefixcommand}` `(nation)`. Leave `nation` empty to view your /linked nation info.",
        description="Use this command to find info about a specific nation.",
    )
    async def n(self, ctx: commands.Context, arg=None):
        if not arg and not await find_linked(ctx.message.author):
            return await ctx.send_help(ctx.command)
        if await is_server_online(ctx) != True:
            return

        wait_msg = await ctx.reply(
            embed=await get_embed(
                ctx=ctx,
                description="<a:happy_red:912452454669508618> Fetching nation data ...",
            )
        )

        if not arg and await (player := find_linked(ctx.message.author)):
            arg = player
        res = requests.get(f"{nationapi}/{arg}")
        embed = await get_embed(ctx, title=f"Nation: {res.json()['name']}")
        embed.add_field(name="King: ", value=res.json()["king"], inline=True)
        embed.add_field(name="Capital: ", value=res.json()["capitalName"], inline=True)
        embed.add_field(name="Claims: ", value=str(res.json()["area"]), inline=False)
        embed.add_field(
            name="Towns: ", value=str(len(res.json()["towns"])), inline=False
        )
        embed.add_field(
            name="Population: ", value=str(len(res.json()["residents"])), inline=False
        )
        await wait_msg.delete()
        await ctx.send(embed=embed)

    @commands.command(
        aliases=["notown"],
        usage="Usage: `prefixcommand`.",
        description="Use this command to get the anme of online players that aren't in a town.",
    )
    async def townless(self, ctx):
        if await is_server_online(ctx) != True:
            return

        wait_msg = await ctx.reply(
            embed=await get_embed(
                ctx=ctx,
                description="<a:happy_red:912452454669508618> Fetching resident data ...",
            )
        )

        res = requests.get(townlessapi)
        li = [res.json()[i]["name"] for i in range(len(res.json()))]
        if li:
            embed = await get_embed(ctx, title="Townless Players")
            embed.add_field(
                name="Names: ", value="```" + "\n".join(li) + "```", inline=False
            )
        else:
            embed = await get_embed(
                ctx,
                description="🚨 No townless players were found.",
                color=discord.Color.red(),
            )
        await wait_msg.delete()
        await ctx.send(embed=embed)

    @commands.command(
        aliases=["server", "jestatus"],
        usage="Usage: `{prefixcommand}`.",
        description="Use this command to get info about the server's network",
    )
    async def status(self, ctx):
        wait_msg = await ctx.reply(
            embed=await get_embed(
                ctx=ctx,
                description="<a:happy_red:912452454669508618> Fetching network status ...",
            )
        )
        res = requests.get(serverapi)
        embed = await get_embed(ctx, title="Network Status")
        embed.add_field(
            name="Towny: ",
            value=f"```{str(res.json()['towny'])}/110```",
            inline=False,
        )
        embed.add_field(
            name="Network: ",
            value=f"```{str(res.json()['online'])}/110```",
            inline=False,
        )
        active = res.json()["serverOnline"]
        if active:
            embed.add_field(name="Server: ", value=":green_circle:", inline=False)
        else:
            embed.add_field(name="Server: ", value=":red_circle:", inline=False)
        await wait_msg.delete()
        await ctx.send(embed=embed)

    @commands.command(
        aliases=["onlineplayer"],
        usage="Usage: `{prefixcommand}`.",
        description="Use this command to get a list of online players.",
    )
    async def online(self, ctx):
        if await is_server_online(ctx) != True:
            return

        wait_msg = await ctx.reply(
            embed=await get_embed(
                ctx=ctx,
                description="<a:happy_red:912452454669508618> Fetching resident data ...",
            )
        )

        res = requests.get(onlineapi)
        embed = await get_embed(ctx, title="Online Players")
        li = [res.json()[i]["name"] for i in range(len(res.json()))]
        embed.add_field(
            name="Names: ", value="```" + "\n".join(li) + "```", inline=False
        )
        await wait_msg.delete()
        await ctx.send(embed=embed)

    @commands.command(
        aliases=["onlinemayors", "mayor", "omayors", "onlinem"],
        usage="Usage: `{prefixcommand}`.",
        description="Use this command to get a list of the mayors that are online in the server.",
    )
    async def mayors(self, ctx):
        if await is_server_online(ctx) != True:
            return

        wait_msg = await ctx.reply(
            embed=await get_embed(
                ctx=ctx,
                description="<a:happy_red:912452454669508618> Fetching mayor data ...",
            )
        )
        res = requests.get(onlineapi)
        embed = await get_embed(ctx, title="Online Mayors")
        li = [
            f"{res.json()[i]['name']}({res.json()[i]['town']})"
            for i in range(len(res.json()))
            if "rank" in res.json()[i] and res.json()[i]["rank"] == "Mayor"
        ]

        embed.add_field(
            name="Names: ", value="```" + "\n".join(li) + "```", inline=False
        )
        await wait_msg.delete()
        await ctx.send(embed=embed)

    @commands.command(
        usage="Usage: `{prefixcommand}` `town`.",
        description="Use this command to view who is online in a town. Leave `town` empty to view your /linked town's info.",
    )
    async def tonline(self, ctx: commands.Context, arg=None):
        if not arg and not await find_linked(ctx.message.author):
            return await ctx.send_help(ctx.command)
        if await is_server_online(ctx) != True:
            return

        wait_msg = await ctx.reply(
            embed=await get_embed(
                ctx=ctx,
                description="<a:happy_red:912452454669508618> Fetching resident data ...",
            )
        )

        if not arg and await (player := find_linked(ctx.message.author)):
            resident = requests.get(f"{townapi}/{player}")
            arg = resident.json()["town"]
        res = requests.get(onlineapi)
        embed = await get_embed(ctx, title=f"Online Players in {arg}")
        li = [
            res.json()[i]["name"]
            for i in range(len(res.json()))
            if "town" in res.json()[i] and res.json()[i]["town"].lower() == arg.lower()
        ]

        embed.add_field(name="Online: ", value=str(len(li)), inline=False)
        if li:
            embed.add_field(
                name="Names: ", value="```" + "\n".join(li) + "```", inline=False
            )
        await wait_msg.delete()
        await ctx.send(embed=embed)

    @commands.command(
        aliases=["ruined", "ruins", "ruin", "ruinedtown"],
        usage="Usage: `{prefixcommand}`.",
        description="Use this command to get the names",
    )
    async def ruinedtowns(self, ctx):
        if await is_server_online(ctx) != True:
            return

        wait_msg = await ctx.reply(
            embed=await get_embed(
                ctx=ctx,
                description="<a:happy_red:912452454669508618> Fetching town data ...",
            )
        )

        res = requests.get(townapi)
        embed = await get_embed(ctx, title="Ruined towns list")
        li = [
            res.json()[i]["name"]
            for i in range(len(res.json()))
            if len(res.json()[i]["residents"]) == 1
            and res.json()[i]["residents"][0][0:3].lower() == "bot"
        ]

        if li:
            embed.add_field(
                name="Town Names: ",
                value="```" + "\n".join(li) + "```",
                inline=False,
            )
        await wait_msg.delete()
        await ctx.send(embed=embed)

    @commands.command(
        aliases=["sieges", "sw", "swar", "war", "siegew", "battles"],
        usage="Usage: `{prefixcommand}` `(sieged town)`.\nLeave town empty to see a list of all sieged towns.",
        description="Use this command to get info about a siege happening at the moment or a list of all sieges.",
    )
    async def siege(self, ctx: commands.Context, arg=None):
        if await is_server_online(ctx) != True:
            return

        wait_msg = await ctx.reply(
            embed=await get_embed(
                ctx=ctx,
                description="<a:happy_red:912452454669508618> Fetching siege data ...",
            )
        )

        res = requests.get(sw)
        if not arg:
            if len(res.json()) > 0:
                a = [res.json()[i]["name"] for i in range(len(res.json()))]
                embed = await get_embed(ctx, title="Sieged Towns: ")
                embed.add_field(
                    name="Town Names", value=f"```{', '.join(a)}```", inline=False
                )
                await wait_msg.delete()
                return await ctx.send(embed=embed)
            else:
                embed = await get_embed(
                    ctx,
                    description="🚨 No towns are being sieged at the moment.",
                    color=discord.Color.red(),
                )
                await wait_msg.delete()
                return await ctx.send(embed=embed)
        for i in range(len(res.json())):
            if res.json()[i]["name"].lower() == arg.lower():
                a = res.json()[i]
                embed = await get_embed(ctx, title="Sieged Town: " + a["name"])
                embed.add_field(name="Attacker", value=a["attacker"], inline=True)
                embed.add_field(name="Type", value=a["type"], inline=True)
                embed.add_field(
                    name="Dynmap",
                    value=f"[{a['x']},{a['z']}](http://jes.enviromc.com:25568/#/?worldname=earth&mapname=flat&zoom=9&x={a['x']}&y=64&z={a['z']})",
                    inline=False,
                )
                embed.add_field(name="Siege Balance", value=a["balance"], inline=False)
                if int(a["balance"]) > 0:
                    embed.add_field(
                        name="Current Winner", value="Attackers", inline=True
                    )
                else:
                    embed.add_field(
                        name="Current Winner", value="Defenders", inline=True
                    )
                embed.add_field(name="Time Left", value=a["time"], inline=False)
                embed.add_field(name="War Chest", value=a["chest"], inline=False)

                await wait_msg.delete()
                await ctx.send(embed=embed)
                return

        embed = await get_embed(
            ctx,
            description="<a:tnt:912834869845958686> This town doesn't exist or isn't besieged...",
            color=discord.Color.red(),
        )
        await ctx.reply(embed=embed)


def setup(bot):
    bot.add_cog(Commands(bot))
