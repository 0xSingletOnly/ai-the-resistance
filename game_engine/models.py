"""
Data models for The Resistance: Avalon game.
"""
from typing import List, Dict, Optional, NamedTuple
from .enums import Role, Team, VoteType, QuestResult

class TeamVoteRecord(NamedTuple):
    """Record of a team vote with context"""
    quest_number: int
    leader: str  # Player name
    proposed_team: List[str]  # List of player names
    vote: VoteType
    quest_result: Optional[QuestResult] = None  # Result of this quest, if completed

class QuestVoteRecord(NamedTuple):
    """Record of a quest vote with context"""
    quest_number: int
    team: List[str]  # List of player names
    vote: VoteType

class Player:
    """Represents a player in the game"""
    
    def __init__(self, name: str):
        self.name = name
        self.role: Optional[Role] = None
        self.team: Optional[Team] = None
        # Enhanced voting history tracking
        self.team_vote_history: List[TeamVoteRecord] = []
        self.quest_vote_history: List[QuestVoteRecord] = []
    
    def assign_role(self, role: Role):
        """Assign a role to the player and set their team accordingly"""
        self.role = role
        if role in [Role.MERLIN, Role.PERCIVAL, Role.LOYAL_SERVANT]:
            self.team = Team.GOOD
        else:
            self.team = Team.EVIL
    
    def add_team_vote(self, vote: VoteType, quest_number: int, leader: str, proposed_team: List[str], quest_result: Optional[QuestResult] = None):
        """Record a team approval vote with context"""
        if vote not in [VoteType.APPROVE, VoteType.REJECT]:
            raise ValueError("Team vote must be APPROVE or REJECT")
        record = TeamVoteRecord(
            quest_number=quest_number,
            leader=leader,
            proposed_team=proposed_team,
            vote=vote,
            quest_result=quest_result
        )
        self.team_vote_history.append(record)
    
    def add_quest_vote(self, vote: VoteType, quest_number: int, team: List[str]):
        """Record a quest vote with context"""
        if vote not in [VoteType.SUCCESS, VoteType.FAIL]:
            raise ValueError("Quest vote must be SUCCESS or FAIL")
        record = QuestVoteRecord(
            quest_number=quest_number,
            team=team,
            vote=vote
        )
        self.quest_vote_history.append(record)
    
    def get_voting_summary(self) -> Dict[str, Dict]:
        """Generate a summary of the player's voting patterns throughout the game"""
        summary = {
            "team_votes": {
                "approve": len([v for v in self.team_vote_history if v.vote == VoteType.APPROVE]),
                "reject": len([v for v in self.team_vote_history if v.vote == VoteType.REJECT]),
                "total": len(self.team_vote_history)
            },
            "quest_votes": {
                "success": len([v for v in self.quest_vote_history if v.vote == VoteType.SUCCESS]),
                "fail": len([v for v in self.quest_vote_history if v.vote == VoteType.FAIL]),
                "total": len(self.quest_vote_history)
            }
        }
        return summary

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
            
        # Record votes in quest's vote tracking
        if vote in [VoteType.APPROVE, VoteType.REJECT]:
            self.pre_quest_votes[player] = vote
            
            # Record vote in player's history with context
            player.add_team_vote(
                vote=vote,
                quest_number=self.quest_number,
                leader=self.leader.name,
                proposed_team=[p.name for p in self.team]
            )
            
        elif vote in [VoteType.SUCCESS, VoteType.FAIL]:
            self.in_quest_votes[player] = vote
            
            # Record vote in player's history with context
            player.add_quest_vote(
                vote=vote,
                quest_number=self.quest_number,
                team=[p.name for p in self.team]
            )
    
    def process_result(self) -> QuestResult:
        """Process the quest result based on votes"""
        fail_votes = sum(1 for vote in self.in_quest_votes.values() if vote == VoteType.FAIL)
        if fail_votes >= self.fails_required:
            self.result = QuestResult.FAIL
        else:
            self.result = QuestResult.SUCCESS

        # Update all team vote records for this quest with the result
        for player, vote in self.pre_quest_votes.items():
            # Remove the old record
            old_record = next(r for r in player.team_vote_history 
                            if r.quest_number == self.quest_number)
            player.team_vote_history.remove(old_record)
            
            # Add new record with quest result
            player.add_team_vote(
                vote=vote,
                quest_number=self.quest_number,
                leader=self.leader.name,
                proposed_team=[p.name for p in self.team],
                quest_result=self.result
            )
        
        return self.result