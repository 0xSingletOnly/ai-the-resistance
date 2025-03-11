"""
Utility functions for The Resistance: Avalon game engine.
"""
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('avalon')


def setup_game_logger(game_id: str, log_dir: str = "logs") -> logging.Logger:
    """
    Set up a logger for a specific game.
    
    Args:
        game_id: Unique identifier for the game
        log_dir: Directory for log files
        
    Returns:
        A configured logger instance
    """
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a unique log file for this game
    log_file = os.path.join(log_dir, f"game_{game_id}.log")
    
    # Create a file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Get a logger for this game
    game_logger = logging.getLogger(f'avalon.game.{game_id}')
    game_logger.addHandler(file_handler)
    
    return game_logger


def log_game_event(logger: logging.Logger, event_type: str, details: Dict[str, Any]):
    """
    Log a game event with structured data.
    
    Args:
        logger: Logger instance
        event_type: Type of event (e.g., 'team_proposed', 'quest_result')
        details: Dictionary of event details
    """
    event_data = {
        "type": event_type,
        "timestamp": datetime.now().isoformat(),
        **details
    }
    logger.info(json.dumps(event_data))


def save_game_state(game_state: Dict[str, Any], game_id: str, save_dir: str = "game_states"):
    """
    Save the game state to a file.
    
    Args:
        game_state: Dictionary representing the game state
        game_id: Unique identifier for the game
        save_dir: Directory for saved game states
    """
    # Create save directory if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)
    
    # Add metadata
    game_state["_meta"] = {
        "saved_at": datetime.now().isoformat(),
        "game_id": game_id
    }
    
    # Create the save file
    save_file = os.path.join(save_dir, f"game_{game_id}.json")
    
    with open(save_file, 'w') as f:
        json.dump(game_state, f, indent=2)


def load_game_state(game_id: str, save_dir: str = "game_states") -> Optional[Dict[str, Any]]:
    """
    Load a game state from a file.
    
    Args:
        game_id: Unique identifier for the game
        save_dir: Directory for saved game states
        
    Returns:
        The game state dictionary if found, None otherwise
    """
    save_file = os.path.join(save_dir, f"game_{game_id}.json")
    
    if not os.path.exists(save_file):
        return None
    
    with open(save_file, 'r') as f:
        return json.load(f)


def generate_game_id() -> str:
    """
    Generate a unique game ID.
    
    Returns:
        A string with a unique game identifier
    """
    return f"avalon_{datetime.now().strftime('%Y%m%d_%H%M%S')}"