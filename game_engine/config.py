"""
Game configuration constants and settings for The Resistance: Avalon.
"""
from typing import Dict, List
from .enums import Team, Role

# Standard role configurations based on player count
ROLE_CONFIGS: Dict[int, Dict] = {
    5: {
        Team.GOOD: 3,  # 3 good players
        Team.EVIL: 2,  # 2 evil players
        "required_roles": [Role.MERLIN, Role.ASSASSIN],
        "optional_roles": [Role.PERCIVAL, Role.MORGANA, Role.MORDRED, Role.OBERON]
    },
    6: {
        Team.GOOD: 4,
        Team.EVIL: 2,
        "required_roles": [Role.MERLIN, Role.ASSASSIN],
        "optional_roles": [Role.PERCIVAL, Role.MORGANA, Role.MORDRED, Role.OBERON]
    },
    7: {
        Team.GOOD: 4,
        Team.EVIL: 3,
        "required_roles": [Role.MERLIN, Role.ASSASSIN],
        "optional_roles": [Role.PERCIVAL, Role.MORGANA, Role.MORDRED, Role.OBERON]
    },
    8: {
        Team.GOOD: 5,
        Team.EVIL: 3,
        "required_roles": [Role.MERLIN, Role.ASSASSIN],
        "optional_roles": [Role.PERCIVAL, Role.MORGANA, Role.MORDRED, Role.OBERON]
    },
    9: {
        Team.GOOD: 6,
        Team.EVIL: 3,
        "required_roles": [Role.MERLIN, Role.ASSASSIN],
        "optional_roles": [Role.PERCIVAL, Role.MORGANA, Role.MORDRED, Role.OBERON]
    },
    10: {
        Team.GOOD: 6,
        Team.EVIL: 4,
        "required_roles": [Role.MERLIN, Role.ASSASSIN],
        "optional_roles": [Role.PERCIVAL, Role.MORGANA, Role.MORDRED, Role.OBERON]
    }
}

# Quest team sizes based on player count
QUEST_CONFIGS: Dict[int, List[int]] = {
    5: [2, 3, 2, 3, 3],
    6: [2, 3, 4, 3, 4],
    7: [2, 3, 3, 4, 4],
    8: [3, 4, 4, 5, 5],
    9: [3, 4, 4, 5, 5],
    10: [3, 4, 4, 5, 5]
}

# Failures required to fail a quest based on player count and quest number (0-indexed)
# Default is 1 fail required, exceptions are specified here
QUEST_FAILURES_REQUIRED: Dict[int, Dict[int, int]] = {
    5: {},  # All quests require 1 failure
    6: {},
    7: {3: 2},  # 4th quest (index 3) requires 2 failures
    8: {3: 2},
    9: {3: 2},
    10: {3: 2, 4: 2}  # Both 4th and 5th quests require 2 failures for 10 players
}

MAX_FAILED_VOTES: int = 5  # Maximum number of consecutive failed team votes before evil wins