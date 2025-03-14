"""
Core data models for The Resistance: Avalon game.

This module contains the foundational data structures used throughout the game:
- Player: Represents a player and their role/team information
- Quest: Represents a single quest attempt and its outcome
- TeamVoteRecord/QuestVoteRecord: Record structures for vote tracking
"""
from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from .enums import Role, Team, VoteType, QuestResult


@dataclass(frozen=True)
class TeamVoteRecord:
    """
    Immutable record of a team vote with context.
    
    Attributes:
        quest_number: The quest number this vote was for (1-based)
        leader: Name of the player who proposed the team
        proposed_team: Names of players proposed for the team
        vote: The vote cast (APPROVE/REJECT)
        quest_result: The final result of this quest, if completed
    """
    quest_number: int
    leader: str
    proposed_team: List[str]
    vote: VoteType
    quest_result: Optional[QuestResult] = None


@dataclass(frozen=True)
class QuestVoteRecord:
    """
    Immutable record of a quest vote with context.
    
    Attributes:
        quest_number: The quest number this vote was for (1-based)
        team: Names of players who went on the quest
        vote: The vote cast (SUCCESS/FAIL)
    """
    quest_number: int
    team: List[str]
    vote: VoteType


class Player:
    """
    Represents a player in the game, tracking their role, team, and voting history.
    
    A player's role and team affiliation determine their victory conditions and
    what information they can see about other players. The voting history allows
    for analysis of player behavior and verification of game outcomes.
    """
    
    def __init__(self, name: str):
        """
        Initialize a new player.
        
        Args:
            name: The player's name, must be unique within a game
        """
        if not name or not isinstance(name, str):
            raise ValueError("Player name must be a non-empty string")
            
        self.name: str = name
        self.role: Optional[Role] = None
        self.team: Optional[Team] = None
        self.team_vote_history: List[TeamVoteRecord] = []
        self.quest_vote_history: List[QuestVoteRecord] = []
    
    def assign_role(self, role: Role) -> None:
        """
        Assign a role to the player and set their team accordingly.
        
        Args:
            role: The role to assign to the player
            
        Raises:
            ValueError: If the role is invalid or already assigned
        """
        if not isinstance(role, Role):
            raise ValueError(f"Invalid role type: {type(role)}")
        if self.role is not None:
            raise ValueError(f"Player {self.name} already has role {self.role}")
        
        self.role = role
        if role in [Role.MERLIN, Role.PERCIVAL, Role.LOYAL_SERVANT]:
            self.team = Team.GOOD
        else:
            self.team = Team.EVIL
    
    def add_team_vote(
        self,
        vote: VoteType,
        quest_number: int,
        leader: str,
        proposed_team: List[str],
        quest_result: Optional[QuestResult] = None
    ) -> None:
        """
        Record a team approval vote with context.
        
        Args:
            vote: The vote cast (must be APPROVE or REJECT)
            quest_number: The quest number this vote was for (1-based)
            leader: Name of the player who proposed the team
            proposed_team: Names of players proposed for the team
            quest_result: Optional final result of the quest
            
        Raises:
            ValueError: If the vote type is invalid for team voting
        """
        if vote not in [VoteType.APPROVE, VoteType.REJECT]:
            raise ValueError("Team vote must be APPROVE or REJECT")
            
        if quest_number < 1:
            raise ValueError("Quest number must be positive")
            
        record = TeamVoteRecord(
            quest_number=quest_number,
            leader=leader,
            proposed_team=proposed_team,
            vote=vote,
            quest_result=quest_result
        )
        self.team_vote_history.append(record)
    
    def add_quest_vote(self, vote: VoteType, quest_number: int, team: List[str]) -> None:
        """
        Record a quest vote with context.
        
        Args:
            vote: The vote cast (must be SUCCESS or FAIL)
            quest_number: The quest number this vote was for (1-based)
            team: Names of players who went on the quest
            
        Raises:
            ValueError: If the vote type is invalid for quest voting
        """
        if vote not in [VoteType.SUCCESS, VoteType.FAIL]:
            raise ValueError("Quest vote must be SUCCESS or FAIL")
            
        if quest_number < 1:
            raise ValueError("Quest number must be positive")
            
        record = QuestVoteRecord(
            quest_number=quest_number,
            team=team,
            vote=vote
        )
        self.quest_vote_history.append(record)
    
    def get_voting_summary(self) -> Dict[str, Dict[str, int]]:
        """
        Generate a summary of the player's voting patterns throughout the game.
        
        Returns:
            Dictionary containing vote counts for both team and quest votes
        """
        return {
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

    def __str__(self) -> str:
        """Return a string representation of the player."""
        role_str = self.role.value if self.role else "Unassigned"
        team_str = self.team.value if self.team else "Unassigned"
        return f"Player: {self.name}, Role: {role_str}, Team: {team_str}"

    def __eq__(self, other: object) -> bool:
        """Compare players based on their names."""
        if not isinstance(other, Player):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        """Hash players based on their names."""
        return hash(self.name)


class Quest:
    """
    Represents a quest in the game, managing team formation and voting.
    
    A quest requires a team of players to be proposed and approved, followed by
    secret voting by the team members to determine the quest's outcome. The number
    of fail votes required to fail the quest varies based on game configuration.
    """
    
    def __init__(self, quest_number: int, required_team_size: int, fails_required: int = 1):
        """
        Initialize a new quest.
        
        Args:
            quest_number: The quest number (1-based)
            required_team_size: Number of players required for the quest
            fails_required: Number of fail votes needed to fail the quest
            
        Raises:
            ValueError: If any parameters are invalid
        """
        if quest_number < 1:
            raise ValueError("Quest number must be positive")
        if required_team_size < 1:
            raise ValueError("Team size must be positive")
        if fails_required < 1:
            raise ValueError("Required fails must be positive")
        if fails_required > required_team_size:
            raise ValueError("Required fails cannot exceed team size")
            
        self.quest_number = quest_number
        self.required_team_size = required_team_size
        self.fails_required = fails_required
        self.team: List[Player] = []
        self.pre_quest_votes: Dict[Player, VoteType] = {}
        self.in_quest_votes: Dict[Player, VoteType] = {}
        self.result: QuestResult = QuestResult.NOT_STARTED
        self.leader: Optional[Player] = None
        self.team_vote_counter = 0
    
    def set_team(self, team: List[Player], leader: Player) -> None:
        """
        Set the team for this quest.
        
        Args:
            team: List of players proposed for the quest
            leader: The player proposing the team
            
        Raises:
            ValueError: If team size is incorrect
        """
        if len(team) != self.required_team_size:
            raise ValueError(f"Team size must be {self.required_team_size}")
            
        if len(set(team)) != len(team):
            raise ValueError("Team cannot contain duplicate players")
            
        self.team = team.copy()
        self.leader = leader
        self.pre_quest_votes.clear()
        self.in_quest_votes.clear()
    
    def add_vote(self, player: Player, vote: VoteType) -> None:
        """
        Add a player's vote for the quest.
        
        Args:
            player: The voting player
            vote: The vote being cast
            
        Raises:
            ValueError: If the vote is invalid or player cannot vote
        """
        if vote in [VoteType.APPROVE, VoteType.REJECT]:
            self.pre_quest_votes[player] = vote
            
            # Record vote in player's history
            player.add_team_vote(
                vote=vote,
                quest_number=self.quest_number,
                leader=self.leader.name,
                proposed_team=[p.name for p in self.team]
            )
            
        elif vote in [VoteType.SUCCESS, VoteType.FAIL]:
            if player not in self.team:
                raise ValueError("Only team members can vote on quest success")
                
            self.in_quest_votes[player] = vote
            
            # Record vote in player's history
            player.add_quest_vote(
                vote=vote,
                quest_number=self.quest_number,
                team=[p.name for p in self.team]
            )
        else:
            raise ValueError(f"Invalid vote type: {vote}")
    
    def process_result(self) -> QuestResult:
        """
        Process the quest result based on votes.
        
        Returns:
            The result of the quest (SUCCESS/FAIL)
            
        Raises:
            ValueError: If not all team members have voted
        """
        if len(self.in_quest_votes) != self.required_team_size:
            raise ValueError("Not all team members have voted")
            
        fail_votes = sum(1 for vote in self.in_quest_votes.values() if vote == VoteType.FAIL)
        self.result = QuestResult.FAIL if fail_votes >= self.fails_required else QuestResult.SUCCESS

        # Update all team vote records with the quest result
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
        
    def __str__(self) -> str:
        """Return a string representation of the quest."""
        status = "Not Started"
        if self.team:
            status = "Team Proposed"
        if self.result != QuestResult.NOT_STARTED:
            status = f"Complete - {self.result.value}"
            
        return (f"Quest {self.quest_number}: {status}, "
                f"Team Size: {self.required_team_size}, "
                f"Fails Required: {self.fails_required}")