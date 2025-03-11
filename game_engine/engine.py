"""
Core game engine for The Resistance: Avalon.
This file now imports from the refactored modules for backward compatibility.
"""
# Re-export all components from their new modules
from .enums import Team, Role, GamePhase, QuestResult, VoteType
from .models import Player, Quest
from .game import AvalonGame

# This allows existing code to continue importing from engine.py without changes
__all__ = ['Team', 'Role', 'GamePhase', 'QuestResult', 'VoteType', 'Player', 'Quest', 'AvalonGame']