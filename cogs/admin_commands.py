import discord
from discord import app_commands
from discord.ext import commands
from utils.question_loader import load_questions
import os

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reload-questions", description="Reload questions from JSON file (Admin only)")
    @app_commands.default_permissions(administrator=True)
    async def reload_questions(self, interaction: discord.Interaction):
        # We don't need to do anything complex here because the random question loader
        # reads from the file or re-loads if we clear a cache.
        # In our simple implementation, get_random_question loads fresh every time 
        # OR we can improve performance by caching. 
        # For this requirement "Reload questions... without restarting":
        
        # NOTE: Our current utils/question_loader.py implementation of 'get_random_question'
        # has a `data=None` argument which calls `load_questions()`.
        # However, to be efficient, `load_questions` reads the file every time.
        # This satisfies the requirement "Add/remove... without breaking... reload dynamically".
        # So essentially, this command just confirms the file is valid.
        
        questions = load_questions()
        
        t_count = len(questions.get("truths", []))
        d_count = len(questions.get("dares", []))
        
        if t_count == 0 and d_count == 0:
             await interaction.response.send_message(
                "⚠️ Warning: `questions.json` appears to be empty or malformed.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"✅ Successfully reloaded questions!\nTruths: {t_count}\nDares: {d_count}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
