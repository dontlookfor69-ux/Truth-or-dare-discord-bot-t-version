import discord
import datetime

def get_rating_color(rating):
    """
    Returns the discord.Color associated with a content rating.
    """
    if not rating:
        return discord.Color.blue()
        
    rating = rating.lower()
    if rating == 'pg':
        return discord.Color.green()
    elif rating == 'pg13':
        return discord.Color.gold()
    elif rating == 'r':
        return discord.Color.red()
    else:
        return discord.Color.blue()

def build_question_embed(question_data, type_str, requestor=None):
    """
    Builds a discord.Embed for a question or dare.
    
    Args:
        question_data (dict): The question object from JSON.
        type_str (str): 'Truth' or 'Dare' (display text).
        requestor (discord.User | discord.Member, optional): The user who requested the question.
        
    Returns:
        discord.Embed: The formatted embed.
    """
    text = question_data.get('question') if 'question' in question_data else question_data.get('dare')
    rating = question_data.get('rating', 'Unknown')
    q_id = question_data.get('id', 'Unknown')
    
    embed = discord.Embed(
        description=text,
        color=get_rating_color(rating),
        timestamp=datetime.datetime.utcnow()
    )
    
    if requestor:
        embed.set_author(name=f"Requested by {requestor.display_name}", icon_url=requestor.display_avatar.url)
    else:
        embed.title = f"🪶 Tickle {type_str}"
    
    embed.set_footer(text=f"Type: {type_str.upper()} | Rating: {rating.upper()} | ID: {q_id}")
    
    return embed
