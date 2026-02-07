import discord
from discord import app_commands
from discord.ext import commands
from utils.question_loader import get_random_question
from utils.embed_builder import build_question_embed
from utils.server_config import set_allowed_channels, get_allowed_channel, get_allowed_ratings
import random

class GameView(discord.ui.View):
    # Rate limit: 1 use per 2 seconds per user
    _cooldowns = {} 

    def __init__(self, mode, rating=None, current_question_id=None):
        super().__init__(timeout=None)
        self.mode = mode 
        self.rating = rating
        self.current_question_id = current_question_id
        
        # Add buttons based on mode
        if mode in ["truth", "dare", "tod"]:
            # Standard TOD buttons
            self.add_button("Truth", discord.ButtonStyle.success, "truth")
            self.add_button("Dare", discord.ButtonStyle.danger, "dare")
            self.add_button("Random", discord.ButtonStyle.primary, "random")
            
        elif mode == "wyr":
             self.add_button("Next WYR", discord.ButtonStyle.primary, "wyr")
             
        elif mode == "nhie":
             self.add_button("Next NHIE", discord.ButtonStyle.primary, "nhie")
             
        elif mode == "paranoia":
             self.add_button("Next Paranoia", discord.ButtonStyle.primary, "paranoia")
             
        elif mode == "random":
             self.add_button("Surprise Me", discord.ButtonStyle.blurple, "random")

    def add_button(self, label, style, type_str):
        button = discord.ui.Button(label=label, style=style)
        
        async def callback(interaction):
            await self.handle_click(interaction, type_str)
            
        button.callback = callback
        self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # 1. Check Rate Limit
        user_id = interaction.user.id
        now = interaction.created_at.timestamp()
        
        last_time = self._cooldowns.get(user_id, 0)
        if now - last_time < 2.0:
            retry_after = 2.0 - (now - last_time)
            await interaction.response.send_message(
                f"⏳ You're clicking too fast! Please wait {retry_after:.1f}s.",
                ephemeral=True
            )
            return False
        
        # 2. Check Allowed Channel and Ratings
        if interaction.guild:
            allowed_config = get_allowed_channel(interaction.guild.id)
            if allowed_config:
                # If config exists, user must be in Main OR NSFW
                main_id = allowed_config.get("main")
                nsfw_id = allowed_config.get("nsfw")
                
                cid = interaction.channel.id
                if cid != main_id and cid != nsfw_id:
                   # Construct helpful message
                   msg = f"⛔ Please play in <#{main_id}>"
                   if nsfw_id:
                       msg += f" or <#{nsfw_id}>"
                   await interaction.response.send_message(msg + "!", ephemeral=True)
                   return False
                
        self._cooldowns[user_id] = now
        if len(self._cooldowns) > 1000: self._cooldowns.clear()
        
        return True

    async def handle_click(self, interaction: discord.Interaction, type_choice: str):
        # Disable previous view
        try:
            await interaction.message.edit(view=None)
        except:
            pass
            
        # Determine allowed ratings for this channel
        allowed_ratings = ["pg", "pg13", "r"] # Default
        if interaction.guild:
            allowed_ratings = get_allowed_ratings(interaction.guild.id, interaction.channel.id)

        # Determine type
        final_type = type_choice
        if type_choice == "random":
            if self.mode == "tod":
                final_type = random.choice(["truth", "dare"])
            elif self.mode == "random":
                final_type = random.choice(["truth", "dare", "wyr", "nhie", "paranoia"])
        
        # Enforce rating on click:
        # If self.rating was set (e.g. they started a "R" game), we try to respect it.
        # But if we are in a channel that doesn't allow "R", we must block or downgrade.
        # Current logic: If self.rating is NOT in allowed_ratings, pick a random allowed rating or fail?
        # Better: If self.rating is explicit (not None) and NOT allowed -> Error.
        # If self.rating is None -> Pick random valid rating question.
        
        target_rating = self.rating
        if target_rating and target_rating not in allowed_ratings:
             # Retain rating but block if invalid?
             # Or auto-switch?
             # For interaction flow (next button), if they started an "R" game in "NSFW" channel,
             # and the button click is still there, it's fine.
             # But if they somehow clicked it elsewhere? (Interaction check handles channel).
             # So if we are in Main (PG only) and self.rating is "r", we should block.
             await interaction.response.send_message("⛔ R-rated content is not allowed in this channel.", ephemeral=True)
             return

        # If target_rating is None (Random rating), we let get_random_question handle filtering?
        # question_loader doesn't take a LIST of allowed ratings, it takes a specific one or None.
        # So filtering needs to happen here or in loader.
        # If target_rating is None, we need to ensure the fetched question is within allowed list.
        # Simple fix: Loop until valid? Or Update loader.
        # Implementation: Loop (simple) or pass filter.
        # Since loader is simple, let's just loop a few times.
        
        question = None
        for _ in range(10):
            q = get_random_question(final_type, target_rating, exclude_id=self.current_question_id)
            if q:
                 if q.get('rating') in allowed_ratings:
                     question = q
                     break
                 # If we requested a specific rating and it wasn't allowed (checked above), we wouldn't be here.
                 # If we requested None, we might get 'r', so we retry.
        
        if not question:
            # Fallback logic
             if type_choice == "random":
                 # Retry loosely
                 final_type = random.choice(["truth", "dare"]) if self.mode == "tod" else "truth"
                 # Try again with same rating logic
                 question = get_random_question(final_type, target_rating)
            
             if not question or (question.get('rating') not in allowed_ratings):
                await interaction.response.send_message("No questions found for allowed ratings!", ephemeral=True)
                return

        embed = build_question_embed(question, final_type.upper(), requestor=interaction.user)
        new_view = GameView(mode=self.mode, rating=self.rating, current_question_id=question.get('id'))
        
        # 10% chance for tip
        content = None
        if random.random() < 0.1:
            content = "<a:tip_emoji:1469795864259330119> Tip: Use /suggest to suggest new questions dares wyr ect !!"
            
        await interaction.response.send_message(content=content, embed=embed, view=new_view)


class GameCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def check_channel_and_rating(self, interaction, requested_rating):
        """
        Checks if the channel is allowed and if the requested rating is permitted.
        Returns (True, allowed_ratings_list) or (False, None).
        Sends ephemeral error if false.
        """
        if not interaction.guild:
            return True, ["pg", "pg13", "r"] # DMs allowed all?
            
        allowed_config = get_allowed_channel(interaction.guild.id)
        if allowed_config:
            main_id = allowed_config.get("main")
            nsfw_id = allowed_config.get("nsfw")
            cid = interaction.channel.id
            
            if cid != main_id and cid != nsfw_id:
                msg = f"⛔ Use <#{main_id}>"
                if nsfw_id: msg += f" or <#{nsfw_id}>"
                await interaction.response.send_message(msg + ".", ephemeral=True)
                return False, None
                
            allowed_ratings = get_allowed_ratings(interaction.guild.id, cid, allowed_config)
            
            if requested_rating and requested_rating not in allowed_ratings:
                await interaction.response.send_message(
                    f"⛔ Rating '{requested_rating.upper()}' is not allowed in this channel.", 
                    ephemeral=True
                )
                return False, None
                
            return True, allowed_ratings
            
        return True, ["pg", "pg13", "r"]

    async def start_game(self, interaction, mode, rating):
        rating_val = rating.value if rating else None
        
        is_allowed, allowed_ratings = await self.check_channel_and_rating(interaction, rating_val)
        if not is_allowed:
            return
            
        # Initial Pick
        type_choice = mode
        if mode == "tod": type_choice = random.choice(["truth", "dare"])
        elif mode == "random": type_choice = random.choice(["truth", "dare", "wyr", "nhie", "paranoia"])
        
        # Fetch question respecting allowed ratings
        question = None
        for _ in range(15):
             q = get_random_question(type_choice, rating_val)
             if q and q.get("rating") in allowed_ratings:
                 question = q
                 break
        
        if not question:
             await interaction.response.send_message("No questions found matching criteria!", ephemeral=True)
             return
             
        embed = build_question_embed(question, type_choice.upper(), requestor=interaction.user)
        
        # If mode is truth or dare, default to TOD view so they can switch
        view_mode = mode
        if mode in ["truth", "dare"]: view_mode = "tod"
        
        view = GameView(mode=view_mode, rating=rating_val, current_question_id=question.get('id'))
        
        # 10% chance for tip
        content = None
        if random.random() < 0.1:
            content = "<a:tip_emoji:1469795864259330119> Tip: Use /suggest to suggest new questions dares wyr ect !!"
            
        await interaction.response.send_message(content=content, embed=embed, view=view)

    @app_commands.command(name="truth", description="Get a random truth")
    @app_commands.describe(rating="Rating")
    @app_commands.choices(rating=[app_commands.Choice(name="PG", value="pg"), app_commands.Choice(name="PG-13", value="pg13"), app_commands.Choice(name="R", value="r")])
    async def truth(self, interaction, rating: app_commands.Choice[str] = None):
        await self.start_game(interaction, "truth", rating)

    @app_commands.command(name="dare", description="Get a random dare")
    @app_commands.describe(rating="Rating")
    @app_commands.choices(rating=[app_commands.Choice(name="PG", value="pg"), app_commands.Choice(name="PG-13", value="pg13"), app_commands.Choice(name="R", value="r")])
    async def dare(self, interaction, rating: app_commands.Choice[str] = None):
        await self.start_game(interaction, "dare", rating)
        
    @app_commands.command(name="tod", description="Random Truth or Dare")
    @app_commands.describe(rating="Rating")
    @app_commands.choices(rating=[app_commands.Choice(name="PG", value="pg"), app_commands.Choice(name="PG-13", value="pg13"), app_commands.Choice(name="R", value="r")])
    async def tod(self, interaction, rating: app_commands.Choice[str] = None):
        await self.start_game(interaction, "tod", rating)
        
    @app_commands.command(name="wyr", description="Would You Rather")
    @app_commands.describe(rating="Rating")
    @app_commands.choices(rating=[app_commands.Choice(name="PG", value="pg"), app_commands.Choice(name="PG-13", value="pg13"), app_commands.Choice(name="R", value="r")])
    async def wyr(self, interaction, rating: app_commands.Choice[str] = None):
        await self.start_game(interaction, "wyr", rating)
        
    @app_commands.command(name="nhie", description="Never Have I Ever")
    @app_commands.describe(rating="Rating")
    @app_commands.choices(rating=[app_commands.Choice(name="PG", value="pg"), app_commands.Choice(name="PG-13", value="pg13"), app_commands.Choice(name="R", value="r")])
    async def nhie(self, interaction, rating: app_commands.Choice[str] = None):
        await self.start_game(interaction, "nhie", rating)

    @app_commands.command(name="paranoia", description="Paranoia Question")
    @app_commands.describe(rating="Rating")
    @app_commands.choices(rating=[app_commands.Choice(name="PG", value="pg"), app_commands.Choice(name="PG-13", value="pg13"), app_commands.Choice(name="R", value="r")])
    async def paranoia(self, interaction, rating: app_commands.Choice[str] = None):
        await self.start_game(interaction, "paranoia", rating)
        
    @app_commands.command(name="random", description="Random from ANY category")
    @app_commands.describe(rating="Rating")
    @app_commands.choices(rating=[app_commands.Choice(name="PG", value="pg"), app_commands.Choice(name="PG-13", value="pg13"), app_commands.Choice(name="R", value="r")])
    async def random_cmd(self, interaction, rating: app_commands.Choice[str] = None):
        await self.start_game(interaction, "random", rating)

    @app_commands.command(name="setup", description="Configure game channels")
    @app_commands.describe(channel="Main channel (PG/PG-13)", nsfw_channel="Optional NSFW channel (Allows R)")
    @app_commands.default_permissions(administrator=True)
    async def setup(self, interaction, channel: discord.TextChannel, nsfw_channel: discord.TextChannel = None):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Perms denied.", ephemeral=True)
        
        nsfw_id = nsfw_channel.id if nsfw_channel else None
        set_allowed_channels(interaction.guild.id, channel.id, nsfw_id)
        
        msg = f"✅ **Setup Complete!**\n🔹 **Main Channel**: {channel.mention} (PG/PG-13)"
        if nsfw_channel:
            msg += f"\n🔸 **NSFW Channel**: {nsfw_channel.mention} (PG/PG-13/R)"
        else:
            msg += "\n(No NSFW channel set - 'R' rating allowed in Main by default? No, logic says if NSFW not set, Main allows All. Wait.)"
            # Correction in display message to match logic
            msg = f"✅ **Setup Complete!**\n🔹 **Game Channel**: {channel.mention} (All Ratings Allowed)"
            
        await interaction.response.send_message(msg, ephemeral=True)

async def setup(bot):
    await bot.add_cog(GameCommands(bot))
