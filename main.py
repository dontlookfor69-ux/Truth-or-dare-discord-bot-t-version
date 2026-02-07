import discord
from discord.ext import commands
import os
import asyncio

# WARNING: Hardcoded token for testing purposes only
# In production, use environment variables or a secure secrets manager
TOKEN = 'PUT_YOUR_TICKLISH_BOT_TOKEN_HERE'

# Setup Intent
intents = discord.Intents.default()
# intents.message_content = True # Not strictly needed for slash commands but good practice

class TickleBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None # Disable default help command
        )

    async def setup_hook(self):
        # Load cogs
        await self.load_extension("cogs.game_commands")
        await self.load_extension("cogs.admin_commands")
        await self.load_extension("cogs.info_commands")
        await self.load_extension("cogs.suggest_commands")
        
        # Sync slash commands
        try:
            guild_id = discord.Object(id=1467699708221980872)
            
            # 1. Clear global commands (removes duplicates if they were previously synced globally)
            # We don't need to explicitly clear if we don't sync global. 
            # But if there ARE old global commands cached, we might want to wipe them.
            # To wipe global commands: self.tree.clear_commands(guild=None) then sync() ?? 
            # Actually, simply running sync() with an empty tree would wipe them, but our tree is NOT empty.
            # So we can't easily wipe global without unregistering cogs first.
            
            # The most common cause of duplicates is having Global + Guild commands.
            # We are copying global -> guild. So we have them as Guild commands.
            # If we also have them as Global commands, they show up twice.
            # To fix, we can just sync the guild. The global ones will eventually disappear if we never sync global again? 
            # No, they stay until overwritten.
            
            # Strategy: Sync BOTH to ensure consistency and remove old global commands.
            # This might take up to an hour for global updates to propagate, but it cleans up the 'tickle-*' commands.
            
            # 1. Sync to Test Guild (Instant update for you)
            self.tree.copy_global_to(guild=guild_id)
            synced_guild = await self.tree.sync(guild=guild_id)
            print(f"Synced {len(synced_guild)} command(s) to guild {guild_id.id}")
            
            # 2. Sync Globally (Removes old /tickle-* commands from the global list)
            print("Syncing global commands... (this may take a moment)")
            synced_global = await self.tree.sync() 
            print(f"Synced {len(synced_global)} global command(s).")
            
        except Exception as e:
            print(f"Failed to sync commands: {e}")

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Logged in as {self.user.name} (ID: {self.user.id})')
        # Setting status to reference the owner
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="over the tickle master"))

    async def on_guild_join(self, guild):
        """
        Event triggered when the bot joins a new server.
        attempts to DM the server owner.
        """
        try:
            owner = guild.owner
            if owner:
                embed = discord.Embed(
                    title="Thank you for adding Tickle Bot!",
                    description="I'm excited to bring some ticklish fun to your server!",
                    color=discord.Color.red()
                )
                
                embed.add_field(
                    name="⚠️ IMPORTANT COMMUNITY RULE ⚠️",
                    value="**This bot contains 18+ content and is NOT allowed to be added to servers with minors.**\n\nBy keeping this bot in your server, you acknowledge that your community is age-appropriate.",
                    inline=False
                )
                
                embed.add_field(
                    name="Get Started",
                    value="Use `/help` to see available commands.",
                    inline=False
                )
                
                await owner.send(embed=embed)
                print(f"Sent welcome DM to owner of guild: {guild.name}")
        except discord.Forbidden:
            print(f"Could not DM owner of guild: {guild.name} (DMs likely closed)")
        except Exception as e:
            print(f"Error acting on guild join: {e}")

def main():
    if TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("ERROR: You must replace 'YOUR_BOT_TOKEN_HERE' in main.py with your actual bot token!")
        return

    bot = TickleBot()
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"Error running bot: {e}")

if __name__ == "__main__":
    main()
