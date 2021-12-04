import discord
from discord.ext import commands
from config import db

config = db["config"]


class CustomHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    async def send_bot_help(ctx):
        townembed = discord.Embed(
            title="Help Menu", color=0x3994E3, description="Get the commands usage."
        )
        townembed.add_field(
            name="Towny related:",
            value="```/t <townname> : Find town informations \n/n <nationname> : Find nation informations \n/res <residentname> : Find resident informations\n/online : Get the online players list\n/townless : get the townless players list\n/mayors : get the online mayors list\n/tonline <townname> : get the online players list of a town\n/ruinedtowns : get the list of ruined towns```",
            inline=False,
        )
        townembed.add_field(
            name="Siegewar related:",
            value="```/siegedtowns : get the list of besieged towns\n/siege <townname> : get informations about a besieged town```",
            inline=False,
        )
        townembed.add_field(
            name="Network related:",
            value="```/status : get the status of the network```",
            inline=False,
        )
        townembed.set_footer(
            text="Made by Vic__dlt and FusedTundra10",
            icon_url="https://yt3.ggpht.com/He93D0q7fCviVoV50_InxmMYYXqDNMkE6JVp3j4kYwUSAFoCPqKOF2RzPLw24DrwVmQJuRZsrhg=s900-c-k-c0x00ffffff-no-rj",
        )
        townembed.set_thumbnail(
            url="https://media.discordapp.net/attachments/829632303239397416/835768717455130624/newicon.png"
        )
        user = ctx.message.author
        townembed.set_author(name=user, icon_url=user.avatar.url)
        await ctx.reply(embed=townembed)
        await ctx.message.delete()

    async def send_command_help(self, command):
        ctx: commands.Context = self.context
        b_config = await config.find_one({"_id": "config"})
        embed = discord.embeds(
            title=f"__**{command.name} help**__",
            description=command.description,
            color=b_config["color"],
        )
        await ctx.send(embed=embed)
