import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random
import string

SUGGESTIONS_FILE = 'data/suggestions.json'
QUESTIONS_FILE = 'questions.json'

def load_suggestions():
    if not os.path.exists(SUGGESTIONS_FILE):
        return []
    try:
        with open(SUGGESTIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_suggestions(suggestions):
    if not os.path.exists('data'):
        os.makedirs('data')
    with open(SUGGESTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(suggestions, f, indent=4)

def add_to_main_questions(text, type_str, rating):
    try:
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        data = {"truths": [], "dares": []}

    type_str = type_str.lower()
    
    if type_str == "truth":
        category = "truths"
    elif type_str == "dare":
        category = "dares"
    elif type_str == "wyr":
        category = "wyr"
    elif type_str == "nhie":
        category = "nhie"
    elif type_str == "paranoia":
        category = "paranoia"
    else:
        category = "truths" # Fallback

    pool = data.get(category, [])
    
    new_id = None
    all_ids = {item.get('id') for item in pool}
    
    while True:
        # Generate 7 random lowercase alphanumeric
        import string
        new_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))
        if new_id not in all_ids:
            break
            
    new_entry = {
        "id": new_id,
        "rating": rating.lower(),
        "question": text 
    }
    
    # Existing logic: "question" if category == "truths" else "dare": text
    # New logic: most are questions. Dares are dares.
    if category == "dares":
        new_entry["dare"] = text
    else:
        new_entry["question"] = text
    
    pool.append(new_entry)
    data[category] = pool # Ensure it's set back
    
    with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    return new_entry

def check_duplicates(text, category):
    from utils.question_loader import load_questions
    import difflib
    
    data = load_questions()
    cat_map = {
        "truth": "truths", 
        "dare": "dares",
        "wyr": "wyr",
        "nhie": "nhie",
        "paranoia": "paranoia"
    }
    key = cat_map.get(category.lower(), "truths")
    pool = data.get(key, [])
    
    similar = []
    text_lower = text.lower()
    
    for item in pool:
        q_text = item.get("question") or item.get("dare")
        if not q_text: continue
            
        ratio = difflib.SequenceMatcher(None, text_lower, q_text.lower()).ratio()
        if ratio >= 0.7: 
            similar.append(f"({int(ratio*100)}%) {q_text[:60]}...")
            
    return similar[:3]

def build_suggestion_embed(sg, index, total):
    embed = discord.Embed(
        title="Suggestion Review",
        description=f"**{sg['type'].upper()}**: {sg['text']}",
        color=discord.Color.orange()
    )
    embed.add_field(name="Suggested Rating", value=sg['rating'].upper())
    embed.add_field(name="User", value=f"{sg['username']} ({sg['user_id']})")
    embed.set_footer(text=f"Suggestion {index + 1}/{total}")
    
    duplicates = check_duplicates(sg['text'], sg['type'])
    if duplicates:
        embed.add_field(
            name="⚠️ Potential Duplicates", 
            value="\n".join(duplicates), 
            inline=False
        )
    return embed

class SuggestionView(discord.ui.View):
    def __init__(self, suggestion_index, author_id):
        super().__init__(timeout=None)
        self.index = suggestion_index
        self.author_id = author_id

    async def update_embed(self, interaction):
        suggestions = load_suggestions()
        if not suggestions or self.index >= len(suggestions):
             await interaction.response.edit_message(content="No more suggestions!", embed=None, view=None)
             return

        sg = suggestions[self.index]
        embed = build_suggestion_embed(sg, self.index, len(suggestions))
        
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("Not authorized", ephemeral=True)
            
        await interaction.response.edit_message(view=RatingView(self.index, self.author_id))

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("Not authorized", ephemeral=True)
            
        await interaction.response.edit_message(view=ConfirmDenyView(self.index, self.author_id))

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.secondary)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("Not authorized", ephemeral=True)
        await interaction.message.delete()

class RatingView(discord.ui.View):
    def __init__(self, index, author_id):
        super().__init__(timeout=None)
        self.index = index
        self.author_id = author_id

    async def confirm_rating(self, interaction, rating):
         await interaction.response.edit_message(view=ConfirmApproveView(self.index, self.author_id, rating))

    @discord.ui.button(label="PG", style=discord.ButtonStyle.primary)
    async def pg(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.confirm_rating(interaction, "pg")

    @discord.ui.button(label="PG-13", style=discord.ButtonStyle.primary)
    async def pg13(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.confirm_rating(interaction, "pg13")

    @discord.ui.button(label="R", style=discord.ButtonStyle.primary)
    async def r(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.confirm_rating(interaction, "r")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=SuggestionView(self.index, self.author_id))

class ConfirmApproveView(discord.ui.View):
    def __init__(self, index, author_id, rating):
        super().__init__(timeout=None)
        self.index = index
        self.author_id = author_id
        self.rating = rating

    @discord.ui.button(label="Confirm Approval", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        suggestions = load_suggestions()
        if self.index >= len(suggestions):
            await interaction.response.send_message("Error: Suggestion not found", ephemeral=True)
            return

        sg = suggestions.pop(self.index)
        save_suggestions(suggestions)
        
        # Add to main questions
        add_to_main_questions(sg['text'], sg['type'], self.rating)
        
        if suggestions:
            new_index = 0 if self.index >= len(suggestions) else self.index
            next_sg = suggestions[new_index]
            embed = build_suggestion_embed(next_sg, new_index, len(suggestions))
            
            await interaction.response.edit_message(embed=embed, view=SuggestionView(new_index, self.author_id))
            await interaction.followup.send(f"✅ Approved and added to DB as {self.rating.upper()}", ephemeral=True)
        else:
            await interaction.response.edit_message(content="✅ All suggestions processed!", embed=None, view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=RatingView(self.index, self.author_id))

class ConfirmDenyView(discord.ui.View):
    def __init__(self, index, author_id):
        super().__init__(timeout=None)
        self.index = index
        self.author_id = author_id

    @discord.ui.button(label="Confirm Deny", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        suggestions = load_suggestions()
        if self.index >= len(suggestions):
             await interaction.response.send_message("Error", ephemeral=True)
             return
             
        suggestions.pop(self.index)
        save_suggestions(suggestions)
        
        if suggestions:
            new_index = 0 if self.index >= len(suggestions) else self.index
            next_sg = suggestions[new_index]
            embed = build_suggestion_embed(next_sg, new_index, len(suggestions))
            
            await interaction.response.edit_message(embed=embed, view=SuggestionView(new_index, self.author_id))
            await interaction.followup.send("❌ Suggestion denied.", ephemeral=True)
        else:
            await interaction.response.edit_message(content="All suggestions processed!", embed=None, view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=SuggestionView(self.index, self.author_id))

class SuggestCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="suggest", description="Suggest a new question or dare")
    @app_commands.describe(type="Is this a question (truth) or dare?", rating="Suggested rating")
    @app_commands.choices(type=[
        app_commands.Choice(name="Truth", value="truth"),
        app_commands.Choice(name="Dare", value="dare"),
        app_commands.Choice(name="Would You Rather", value="wyr"),
        app_commands.Choice(name="Never Have I Ever", value="nhie"),
        app_commands.Choice(name="Paranoia", value="paranoia")
    ], rating=[
        app_commands.Choice(name="PG", value="pg"),
        app_commands.Choice(name="PG-13", value="pg13"),
        app_commands.Choice(name="R", value="r")
    ])
    async def suggest(self, interaction: discord.Interaction, text: str, type: app_commands.Choice[str], rating: app_commands.Choice[str]):
        suggestions = load_suggestions()
        suggestion = {
            "text": text,
            "type": type.value,
            "rating": rating.value,
            "user_id": interaction.user.id,
            "username": interaction.user.name,
            "id": len(suggestions) + 1
        }
        suggestions.append(suggestion)
        save_suggestions(suggestions)
        
        await interaction.response.send_message("✅ Suggestion submitted for review!", ephemeral=True)

    @app_commands.command(name="approve-cycle", description="Review suggestions (Authorized users only)")
    @app_commands.default_permissions(administrator=True)
    async def approve_cycle(self, interaction: discord.Interaction):
        # Check Authorization
        AUTHORIZED_USER_ID = 1467691908506583132
        if interaction.user.id != AUTHORIZED_USER_ID:
            await interaction.response.send_message("⛔ You are not authorized to use this command.", ephemeral=True)
            return

        suggestions = load_suggestions()
        if not suggestions:
            await interaction.response.send_message("No pending suggestions.", ephemeral=True)
            return

        # Start with the first suggestion
        index = 0
        sg = suggestions[index]
        
        embed = build_suggestion_embed(sg, index, len(suggestions))
        
        view = SuggestionView(index, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(SuggestCommands(bot))
