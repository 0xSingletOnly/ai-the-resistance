"""
Main game engine for The Resistance: Avalon.
"""
import random
from typing import List, Dict, Optional, Set, Tuple
from .enums import Team, Role, GamePhase, QuestResult, VoteType
from .models import Player, Quest, TeamVoteRecord
from .config import ROLE_CONFIGS, QUEST_CONFIGS, QUEST_FAILURES_REQUIRED, MAX_FAILED_VOTES

class AvalonGame:
    """
    Main game class for The Resistance: Avalon.
    
    This class manages the core game logic including:
    - Player and role management
    - Quest progression and voting
    - Game state tracking
    - Victory conditions
    
    The game follows a strict phase progression:
    SETUP -> TEAM_BUILDING -> TEAM_VOTING -> QUEST -> ASSASSINATION/GAME_END
    """
    
    def __init__(self, player_names: List[str], custom_roles: Optional[Dict[Role, int]] = None):
        """
        Initialize a new game of Avalon.
        
        Args:
            player_names: List of player names to participate in the game
            custom_roles: Optional dictionary mapping roles to quantities for custom game setup
            
        Raises:
            ValueError: If player count is invalid or custom roles configuration is incorrect
        """
        if not (5 <= len(player_names) <= 10):
            raise ValueError("Player count must be between 5 and 10")
            
        self.players = [Player(name) for name in player_names]
        self.player_count = len(self.players)
        self.quests = self._setup_quests()
        self.current_quest_idx = 0
        self.current_leader_idx = random.randint(0, self.player_count - 1)
        self.phase = GamePhase.SETUP
        self.failed_votes_count = 0
        self.succeeded_quests = 0
        self.failed_quests = 0
        self.assassin: Optional[Player] = None
        self.assassinated_player: Optional[Player] = None
        
        if custom_roles:
            self._validate_custom_roles(custom_roles)
            self._assign_custom_roles(custom_roles)
        else:
            self._assign_default_roles()
    
    def _setup_quests(self) -> List[Quest]:
        """Set up the quests configuration for the current player count."""
        quest_sizes = QUEST_CONFIGS[self.player_count]
        failures_required_config = QUEST_FAILURES_REQUIRED[self.player_count]
        return [
            Quest(i + 1, size, failures_required_config.get(i, 1))
            for i, size in enumerate(quest_sizes)
        ]
    
    def _validate_custom_roles(self, custom_roles: Dict[Role, int]) -> None:
        """
        Validate that the custom role configuration is valid for the player count.
        
        Args:
            custom_roles: Dictionary mapping roles to their quantities
            
        Raises:
            ValueError: If the role configuration is invalid
        """
        role_counts = {Team.GOOD: 0, Team.EVIL: 0}
        for role, count in custom_roles.items():
            team = Team.GOOD if role in [Role.MERLIN, Role.PERCIVAL, Role.LOYAL_SERVANT] else Team.EVIL
            role_counts[team] += count
        
        config = ROLE_CONFIGS[self.player_count]
        if role_counts[Team.GOOD] != config[Team.GOOD]:
            raise ValueError(f"Custom roles must include exactly {config[Team.GOOD]} good roles")
        if role_counts[Team.EVIL] != config[Team.EVIL]:
            raise ValueError(f"Custom roles must include exactly {config[Team.EVIL]} evil roles")
    
    def _assign_default_roles(self) -> None:
        """Assign default roles based on the current player count."""
        config = ROLE_CONFIGS[self.player_count]
        roles = config["required_roles"].copy()
        
        # Fill remaining good roles with Loyal Servants
        good_roles_needed = config[Team.GOOD] - sum(1 for role in roles if role in [Role.MERLIN, Role.PERCIVAL])
        roles.extend([Role.LOYAL_SERVANT] * good_roles_needed)
        
        # Fill remaining evil roles with Minions
        evil_roles_needed = config[Team.EVIL] - sum(1 for role in roles if role not in [Role.MERLIN, Role.PERCIVAL, Role.LOYAL_SERVANT])
        roles.extend([Role.MINION] * evil_roles_needed)
        
        self._assign_roles(roles)
    
    def _assign_custom_roles(self, custom_roles: Dict[Role, int]) -> None:
        """
        Assign custom roles to players.
        
        Args:
            custom_roles: Dictionary mapping roles to their quantities
        """
        roles = []
        for role, count in custom_roles.items():
            roles.extend([role] * count)
        self._assign_roles(roles)
    
    def _assign_roles(self, roles: List[Role]) -> None:
        """
        Assign the given roles randomly to players.
        
        Args:
            roles: List of roles to assign
        """
        random.shuffle(roles)
        for player, role in zip(self.players, roles):
            player.assign_role(role)
            if role == Role.ASSASSIN:
                self.assassin = player
    
    def get_current_quest(self) -> Quest:
        """Get the current active quest."""
        return self.quests[self.current_quest_idx]
    
    def get_current_leader(self) -> Player:
        """Get the current team leader."""
        return self.players[self.current_leader_idx]
    
    def advance_leader(self) -> None:
        """Move leadership to the next player."""
        self.current_leader_idx = (self.current_leader_idx + 1) % self.player_count
    
    def propose_team(self, leader: Player, team: List[Player]) -> Quest:
        """
        Leader proposes a team for the current quest.
        
        Args:
            leader: The player proposing the team
            team: List of players for the quest
            
        Returns:
            The current quest with the proposed team
            
        Raises:
            ValueError: If the proposal is invalid or made at wrong phase
        """
        if self.phase != GamePhase.TEAM_BUILDING:
            raise ValueError(f"Cannot propose team in {self.phase.value} phase")
        if leader != self.get_current_leader():
            raise ValueError("Only the leader can propose a team")
        
        current_quest = self.get_current_quest()
        current_quest.set_team(team, leader)
        self.phase = GamePhase.TEAM_VOTING
        return current_quest
    
    def vote_for_team(self, player: Player, vote: VoteType) -> None:
        """
        Player votes for the proposed team.
        
        Args:
            player: The voting player
            vote: The player's vote (APPROVE/REJECT)
            
        Raises:
            ValueError: If the vote is invalid or made at wrong phase
        """
        if self.phase != GamePhase.TEAM_VOTING:
            raise ValueError(f"Cannot vote for team in {self.phase.value} phase")
        if vote not in [VoteType.APPROVE, VoteType.REJECT]:
            raise ValueError("Team vote must be APPROVE or REJECT")
        
        current_quest = self.get_current_quest()
        current_quest.add_vote(player, vote)
        
        if len(current_quest.pre_quest_votes) == self.player_count:
            self._process_team_votes()
    
    def _process_team_votes(self) -> None:
        """Process team votes and update game state accordingly."""
        current_quest = self.get_current_quest()
        approve_votes = sum(1 for vote in current_quest.pre_quest_votes.values() if vote == VoteType.APPROVE)
        
        if approve_votes > self.player_count / 2:
            self.failed_votes_count = 0
            self.phase = GamePhase.QUEST
        else:
            self.failed_votes_count += 1
            current_quest.team_vote_counter += 1
            self.advance_leader()
            
            if self.failed_votes_count >= MAX_FAILED_VOTES:
                self.phase = GamePhase.GAME_END
                return
            
            self.phase = GamePhase.TEAM_BUILDING
    
    def vote_on_quest(self, player: Player, vote: VoteType) -> None:
        """
        Team member votes on the quest outcome.
        
        Args:
            player: The voting player
            vote: The player's vote (SUCCESS/FAIL)
            
        Raises:
            ValueError: If the vote is invalid or made at wrong phase
        """
        if self.phase != GamePhase.QUEST:
            raise ValueError(f"Cannot vote on quest in {self.phase.value} phase")
        if vote not in [VoteType.SUCCESS, VoteType.FAIL]:
            raise ValueError("Quest vote must be SUCCESS or FAIL")
        if vote == VoteType.FAIL and player.team != Team.EVIL:
            raise ValueError("Good players cannot vote to fail quests")
        
        current_quest = self.get_current_quest()
        if player not in current_quest.team:
            raise ValueError("Only team members can vote on the quest")
        
        current_quest.add_vote(player, vote)
        
        if len(current_quest.in_quest_votes) == current_quest.required_team_size:
            result = current_quest.process_result()
            self.succeeded_quests += (result == QuestResult.SUCCESS)
            self.failed_quests += (result == QuestResult.FAIL)
            self._process_quest_result()
    
    def _process_quest_result(self) -> None:
        """Update game state based on quest result."""
        current_quest = self.get_current_quest()
        result = current_quest.result
        
        # Update quest results in team vote history
        for player in self.players:
            for i, vote in enumerate(player.team_vote_history):
                if vote.quest_number == current_quest.quest_number:
                    player.team_vote_history[i] = TeamVoteRecord(
                        quest_number=vote.quest_number,
                        leader=vote.leader,
                        proposed_team=vote.proposed_team,
                        vote=vote.vote,
                        quest_result=result
                    )
        
        if self.succeeded_quests >= 3:
            self.phase = GamePhase.ASSASSINATION
        elif self.failed_quests >= 3:
            self.phase = GamePhase.GAME_END
        else:
            self.current_quest_idx += 1
            self.advance_leader()
            self.phase = GamePhase.TEAM_BUILDING
    
    def assassinate(self, target: Player) -> None:
        """
        Assassin attempts to identify and eliminate Merlin.
        
        Args:
            target: The player targeted for assassination
            
        Raises:
            ValueError: If assassination attempt is invalid or made at wrong phase
        """
        if self.phase != GamePhase.ASSASSINATION:
            raise ValueError(f"Cannot assassinate in {self.phase.value} phase")
        if not self.assassin:
            raise ValueError("No assassin in the game")
        
        self.assassinated_player = target
        self.phase = GamePhase.GAME_END
    
    def is_game_over(self) -> bool:
        """Check if the game has ended."""
        return self.phase == GamePhase.GAME_END
    
    def get_winner(self) -> Optional[Team]:
        """
        Determine the winning team.
        
        Returns:
            The winning team, or None if game is not over
        """
        if not self.is_game_over():
            return None
        
        if self.failed_quests >= 3:
            return Team.EVIL
        
        if self.assassinated_player and self.assassinated_player.role == Role.MERLIN:
            return Team.EVIL
        
        return Team.GOOD
    
    def get_visible_roles(self, player: Player) -> Dict[Player, Role]:
        """
        Get the roles visible to a specific player based on their role.
        
        Args:
            player: The player whose viewpoint to use
            
        Returns:
            Dictionary mapping visible players to their roles
        """
        visible_roles = {player: player.role}
        
        if player.role == Role.MERLIN:
            # Merlin sees all evil players except Mordred
            visible_roles.update({
                p: Role.MINION
                for p in self.players
                if p.team == Team.EVIL and p.role != Role.MORDRED
            })
            
        elif player.role == Role.PERCIVAL:
            # Percival sees Merlin and Morgana
            visible_roles.update({
                p: Role.MERLIN
                for p in self.players
                if p.role in [Role.MERLIN, Role.MORGANA]
            })
            
        elif player.team == Team.EVIL and player.role != Role.OBERON:
            # Evil players (except Oberon) see other evil players
            visible_roles.update({
                p: p.role
                for p in self.players
                if p.team == Team.EVIL and p.role != Role.OBERON and p != player
            })
        
        return visible_roles
    
    def get_game_state(self, for_player: Optional[Player] = None) -> Dict:
        """
        Get the current game state, optionally from a specific player's perspective.
        
        Args:
            for_player: If provided, return only information visible to this player
            
        Returns:
            Dictionary containing the current game state
        """
        state = {
            "phase": self.phase.value,
            "current_quest_number": self.current_quest_idx + 1,
            "succeeded_quests": self.succeeded_quests,
            "failed_quests": self.failed_quests,
            "current_leader": self.get_current_leader().name,
            "failed_votes_count": self.failed_votes_count,
            "current_quest": {
                "required_team_size": self.get_current_quest().required_team_size,
                "fails_required": self.get_current_quest().fails_required,
                "team": [p.name for p in self.get_current_quest().team] if self.get_current_quest().team else []
            }
        }
        
        if for_player:
            state.update({
                "role": for_player.role.value,
                "team": for_player.team.value,
                "visible_roles": {
                    p.name: r.value 
                    for p, r in self.get_visible_roles(for_player).items()
                },
                "voting_history": {
                    "team_votes": [
                        {
                            "quest": record.quest_number,
                            "leader": record.leader,
                            "proposed_team": record.proposed_team,
                            "vote": record.vote.value,
                            "quest_result": record.quest_result.value if record.quest_result else None
                        }
                        for record in for_player.team_vote_history
                    ]
                }
            })
            
            if self.phase == GamePhase.GAME_END:
                state["voting_history"]["quest_votes"] = [
                    {
                        "quest": record.quest_number,
                        "team": record.team,
                        "vote": record.vote.value
                    }
                    for record in for_player.quest_vote_history
                ]
        else:
            state["players"] = {
                p.name: {
                    "role": p.role.value,
                    "team": p.team.value,
                    "team_votes": [
                        {
                            "quest": record.quest_number,
                            "leader": record.leader,
                            "proposed_team": record.proposed_team,
                            "vote": record.vote.value,
                            "quest_result": record.quest_result.value if record.quest_result else None
                        }
                        for record in p.team_vote_history
                    ]
                }
                for p in self.players
            }
            
            if self.phase == GamePhase.GAME_END:
                for p_name, p_state in state["players"].items():
                    player = next(p for p in self.players if p.name == p_name)
                    p_state["quest_votes"] = [
                        {
                            "quest": record.quest_number,
                            "team": record.team,
                            "vote": record.vote.value
                        }
                        for record in player.quest_vote_history
                    ]
        
        if self.phase == GamePhase.GAME_END:
            state["winner"] = self.get_winner().value if self.get_winner() else None
        
        return state

    def _set_dummy_phase(self, phase: GamePhase) -> None:
        """Helper method for testing - allows direct phase manipulation."""
        self.phase = phase