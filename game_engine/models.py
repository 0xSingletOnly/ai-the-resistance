"""
Data models for The Resistance: Avalon game.
"""
from typing import List, Dict, Optional
from .enums import Role, Team, VoteType, QuestResult
class Player:
    """Represents a player in the game"""
    
    def __init__(self, name: str):
        self.name = name
        self.role: Optional[Role] = None
        self.team: Optional[Team] = None
    
    def assign_role(self, role: Role):
        """Assign a role to the player and set their team accordingly"""
        self.role = role
        if role in [Role.MERLIN, Role.PERCIVAL, Role.LOYAL_SERVANT]:
            self.team = Team.GOOD
        else:
            self.team = Team.EVIL
    
    def __str__(self) -> str:
        return f"Player: {self.name}, Role: {self.role}, Team: {self.team}"

class Quest:
    """Represents a quest in the game"""
    
    def __init__(self, quest_number: int, required_team_size: int, fails_required: int = 1):
        self.quest_number = quest_number
        self.required_team_size = required_team_size
        self.fails_required = fails_required  # Number of fail votes required for the quest to fail
        self.team: List[Player] = []
        self.pre_quest_votes: Dict[Player, VoteType] = {}
        self.in_quest_votes: Dict[Player, VoteType] = {}
        self.result: QuestResult = QuestResult.NOT_STARTED
        self.leader: Optional[Player] = None
        self.team_vote_counter = 0  # Count of team proposal votes that have failed
    
    def set_team(self, team: List[Player], leader: Player):
        """Set the team for this quest"""
        if len(team) != self.required_team_size:
            raise ValueError(f"Team size must be {self.required_team_size}")
        self.team = team
        self.leader = leader
        self.pre_quest_votes = {}
        self.in_quest_votes = {}
    
    def add_vote(self, player: Player, vote: VoteType):
        """Add a player's vote for the quest"""
        if player not in self.team and vote in [VoteType.SUCCESS, VoteType.FAIL]:
            raise ValueError("Only team members can vote on quest success")
        if vote in [VoteType.APPROVE, VoteType.REJECT]:
            self.pre_quest_votes[player] = vote
        elif vote in [VoteType.SUCCESS, VoteType.FAIL]:
            self.in_quest_votes[player] = vote
    
    def process_result(self) -> QuestResult:
        """Process the quest result based on votes"""
        fail_votes = sum(1 for vote in self.in_quest_votes.values() if vote == VoteType.FAIL)
        if fail_votes >= self.fails_required:
            self.result = QuestResult.FAIL
        else:
            self.result = QuestResult.SUCCESS
        return self.result