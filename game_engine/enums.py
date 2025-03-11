"""
Enumerations for The Resistance: Avalon game.
"""
from enum import Enum


class Team(Enum):
    """Team affiliations in Avalon"""
    GOOD = "Good"  # Loyal Servants of Arthur
    EVIL = "Evil"  # Minions of Mordred


class Role(Enum):
    """Character roles in Avalon"""
    # Good Roles
    MERLIN = "Merlin"  # Knows the evil players
    PERCIVAL = "Percival"  # Knows who Merlin is
    LOYAL_SERVANT = "Loyal Servant of Arthur"  # Basic good role
    
    # Evil Roles
    ASSASSIN = "Assassin"  # Can assassinate Merlin at the end
    MORGANA = "Morgana"  # Appears as Merlin to Percival
    MORDRED = "Mordred"  # Hidden from Merlin
    OBERON = "Oberon"  # Hidden from other evil players
    MINION = "Minion of Mordred"  # Basic evil role


class GamePhase(Enum):
    """Phases of the game"""
    SETUP = "Setup"
    TEAM_BUILDING = "Team Building"
    TEAM_VOTING = "Team Voting" 
    QUEST = "Quest"
    ASSASSINATION = "Assassination"
    GAME_END = "Game End"


class QuestResult(Enum):
    """Possible outcomes of a quest"""
    SUCCESS = "Success"
    FAIL = "Fail"
    PENDING = "Pending"
    NOT_STARTED = "Not Started"


class VoteType(Enum):
    """Types of votes that can occur in the game"""
    APPROVE = "Approve"
    REJECT = "Reject"
    SUCCESS = "Success"
    FAIL = "Fail"