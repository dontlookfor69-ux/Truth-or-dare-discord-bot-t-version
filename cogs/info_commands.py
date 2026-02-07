import discord
from discord import app_commands
from discord.ext import commands
from utils.question_loader import load_questions

class InfoCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tickle-stats", description="Show statistics about the question pool")
    async def tickle_stats(self, interaction: discord.Interaction):
        questions = load_questions()
        
        categories = ["truths", "dares", "wyr", "nhie", "paranoia"]
        embed = discord.Embed(
            title="📊 Tickle Bot Stats",
            color=discord.Color.blurple()
        )
        
        total_questions = 0
        
        for cat in categories:
            items = questions.get(cat, [])
            count = len(items)
            total_questions += count
            
            pg = len([q for q in items if q.get("rating", "").lower() == "pg"])
            pg13 = len([q for q in items if q.get("rating", "").lower() == "pg13"])
            r = len([q for q in items if q.get("rating", "").lower() == "r"])
            
            # Format title nicely (e.g. "nhie" -> "NHIE", "wyr" -> "WYR")
            title = cat.upper() if cat in ["wyr", "nhie"] else cat.capitalize()
            
            embed.add_field(
                name=title,
                value=f"**Total: {count}**\nPG: {pg}\nPG-13: {pg13}\nR: {r}",
                inline=True
            )
            
        embed.description = f"**Total Questions in Database: {total_questions}**"
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="Show available commands")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="❓ Tickle Bot Help",
            description=(
                "**How to Play:**\n"
                "• **Everyone**: Use any of the commands below to start a game!\n"
                "• **Buttons**: Click the buttons to continue playing.\n\n"
                "**⚠️ IMPORTANT RULES:**\n"
                "This bot contains **18+ content** and is strictly prohibited in servers with minors.\n"
                "By using this bot, you agree to keep your community age-appropriate.\n\n"
                "**Available Commands:**"
            ),
            color=discord.Color.green()
        )
        
        embed.add_field(name="/truth [rating]", value="Get a random truth question.", inline=True)
        embed.add_field(name="/dare [rating]", value="Get a random dare.", inline=True)
        embed.add_field(name="/tod [rating]", value="Random Truth or Dare.", inline=True)
        embed.add_field(name="/wyr [rating]", value="Would You Rather?", inline=True)
        embed.add_field(name="/nhie [rating]", value="Never Have I Ever.", inline=True)
        embed.add_field(name="/paranoia [rating]", value="Paranoia question.", inline=True)
        embed.add_field(name="/random [rating]", value="Random question from ANY category.", inline=False)
        
        embed.add_field(
            name="/tickle-stats",
            value="View stats about questions in the database.",
            inline=False
        )
        
        embed.add_field(
            name="🔒 Admin Commands",
            value=(
                "• **/setup [channel] [nsfw_channel]**: Configure game channels. If NSFW channel is set, R-rated content is restricted to it.\n"
                "• **/reload-questions**: Reload the questions file.\n"
                "• **/approve-cycle**: Review user suggestions."
            ),
            inline=False
        )
        
        embed.add_field(
            name="Bot Owner",
            value="<@1467691908506583132>",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(InfoCommands(bot))
