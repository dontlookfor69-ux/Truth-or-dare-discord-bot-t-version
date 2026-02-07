import json
import os

CONFIG_FILE = 'data/server_config.json'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_config(config):
    if not os.path.exists('data'):
        os.makedirs('data')
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

def get_allowed_channel(guild_id):
    """
    Returns a dict with 'main' and 'nsfw' keys, or None if not set.
    Example: {'main': 123, 'nsfw': 456} or {'main': 123, 'nsfw': None}
    """
    config = load_config()
    val = config.get(str(guild_id))
    
    if val is None:
        return None
        
    # Backward compatibility: if it's an int, treat as main channel only
    if isinstance(val, int):
        return {"main": val, "nsfw": None}
        
    return val

def set_allowed_channels(guild_id, main_id, nsfw_id=None):
    config = load_config()
    config[str(guild_id)] = {"main": main_id, "nsfw": nsfw_id}
    save_config(config)

def get_allowed_ratings(guild_id, channel_id, allowed_config=None):
    """
    Returns a list of allowed ratings (['pg', 'pg13', 'r']) for the given channel.
    If no config is set, all ratings are allowed.
    """
    if allowed_config is None:
        allowed_config = get_allowed_channel(guild_id)
        
    if not allowed_config:
        return ["pg", "pg13", "r"]
        
    main_id = allowed_config.get("main")
    nsfw_id = allowed_config.get("nsfw")
    
    # If channel matches NSFW channel, allow everything
    if nsfw_id and channel_id == nsfw_id:
        return ["pg", "pg13", "r"]
        
    # If channel matches Main channel
    if main_id and channel_id == main_id:
        # If NSFW channel is set, Main is restricted to PG/PG13
        if nsfw_id:
            return ["pg", "pg13"]
        # If NO NSFW channel set, Main allows everything
        return ["pg", "pg13", "r"]
        
    # If channel matches neither, allow nothing (should be blocked before this)
    return []
