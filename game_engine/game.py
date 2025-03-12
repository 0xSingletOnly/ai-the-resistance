"""
Main game engine for The Resistance: Avalon.
"""
import random
from typing import List, Dict, Optional, Set, Tuple
from .enums import Team, Role, GamePhase, QuestResult, VoteType
from .models import Player, Quest

class AvalonGame:
    """Main game class for The Resistance: Avalon"""
    
    # Standard role configurations based on player count
    ROLE_CONFIGS = {
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
    QUEST_CONFIGS = {
        5: [2, 3, 2, 3, 3],
        6: [2, 3, 4, 3, 4],
        7: [2, 3, 3, 4, 4],
        8: [3, 4, 4, 5, 5],
        9: [3, 4, 4, 5, 5],
        10: [3, 4, 4, 5, 5]
    }
    
    # Failures required to fail a quest based on player count and quest number (0-indexed)
    # Default is 1 fail required, exceptions are specified here
    QUEST_FAILURES_REQUIRED = {
        5: {},  # All quests require 1 failure
        6: {},
        7: {3: 2},  # 4th quest (index 3) requires 2 failures
        8: {3: 2},
        9: {3: 2},
        10: {3: 2, 4: 2}  # Both 4th and 5th quests require 2 failures for 10 players
    }
    
    def __init__(self, player_names: List[str], custom_roles: Dict[Role, int] = None):
        """
        Initialize the game with player names and optional custom roles.
        
        Args:
            player_names: List of player names
            custom_roles: Optional dictionary mapping roles to quantities
        """
        self.players = [Player(name) for name in player_names]
        self.player_count = len(self.players)
        
        if self.player_count < 5 or self.player_count > 10:
            raise ValueError("Player count must be between 5 and 10")
        
        self.quests = self._setup_quests()
        self.current_quest_idx = 0
        self.current_leader_idx = random.randint(0, self.player_count - 1)
        self.phase = GamePhase.SETUP
        self.failed_votes_count = 0  # Track consecutive failed team votes
        
        # Track succeeded and failed quests
        self.succeeded_quests = 0
        self.failed_quests = 0
        
        # For assassination phase
        self.assassin = None
        self.assassinated_player = None
        
        if custom_roles:
            self._validate_custom_roles(custom_roles)
            self._assign_custom_roles(custom_roles)
        else:
            self._assign_default_roles()
    
    def _setup_quests(self) -> List[Quest]:
        """Set up the quests based on player count"""
        quest_sizes = self.QUEST_CONFIGS[self.player_count]
        failures_required_config = self.QUEST_FAILURES_REQUIRED[self.player_count]
        quests = []
        
        for i, size in enumerate(quest_sizes):
            # Get the failures required for this quest (default to 1 if not specified)
            fails_required = failures_required_config.get(i, 1)
            quests.append(Quest(i + 1, size, fails_required))
        
        return quests
    
    def _validate_custom_roles(self, custom_roles: Dict[Role, int]):
        """Validate the custom role configuration"""
        role_counts = {Team.GOOD: 0, Team.EVIL: 0}
        
        for role, count in custom_roles.items():
            if role in [Role.MERLIN, Role.PERCIVAL, Role.LOYAL_SERVANT]:
                role_counts[Team.GOOD] += count
            else:
                role_counts[Team.EVIL] += count
        
        expected_good = self.ROLE_CONFIGS[self.player_count][Team.GOOD]
        expected_evil = self.ROLE_CONFIGS[self.player_count][Team.EVIL]
        
        if role_counts[Team.GOOD] != expected_good:
            raise ValueError(f"Custom roles must include exactly {expected_good} good roles")
        
        if role_counts[Team.EVIL] != expected_evil:
            raise ValueError(f"Custom roles must include exactly {expected_evil} evil roles")
    
    def _assign_default_roles(self):
        """Assign default roles based on player count"""
        # Get configuration for this player count
        config = self.ROLE_CONFIGS[self.player_count]
        
        # Always include required roles
        roles = config["required_roles"].copy()
        
        # Fill remaining good roles with Loyal Servants
        good_roles_needed = config[Team.GOOD] - sum(1 for role in roles if role in [Role.MERLIN, Role.PERCIVAL])
        roles.extend([Role.LOYAL_SERVANT] * good_roles_needed)
        
        # Fill remaining evil roles with Minions
        evil_roles_needed = config[Team.EVIL] - sum(1 for role in roles if role not in [Role.MERLIN, Role.PERCIVAL, Role.LOYAL_SERVANT])
        roles.extend([Role.MINION] * evil_roles_needed)
        
        # Shuffle roles and assign to players
        random.shuffle(roles)
        for player, role in zip(self.players, roles):
            player.assign_role(role)
            if role == Role.ASSASSIN:
                self.assassin = player
    
    def _assign_custom_roles(self, custom_roles: Dict[Role, int]):
        """Assign custom roles to players"""
        roles = []
        for role, count in custom_roles.items():
            roles.extend([role] * count)
        
        # Shuffle roles and assign to players
        random.shuffle(roles)
        for player, role in zip(self.players, roles):
            player.assign_role(role)
            if role == Role.ASSASSIN:
                self.assassin = player
    
    def get_current_quest(self) -> Quest:
        """Get the current quest"""
        return self.quests[self.current_quest_idx]
    
    def get_current_leader(self) -> Player:
        """Get the current leader"""
        return self.players[self.current_leader_idx]
    
    def advance_leader(self):
        """Move to the next leader"""
        self.current_leader_idx = (self.current_leader_idx + 1) % self.player_count
    
    def propose_team(self, leader: Player, team: List[Player]):
        """Leader proposes a team for the current quest"""
        if self.phase != GamePhase.TEAM_BUILDING:
            raise ValueError(f"Cannot propose team in {self.phase.value} phase")
        
        if leader != self.get_current_leader():
            raise ValueError("Only the leader can propose a team")
        
        current_quest = self.get_current_quest()
        current_quest.set_team(team, leader)
        self.phase = GamePhase.TEAM_VOTING
        return current_quest
    
    def vote_for_team(self, player: Player, vote: VoteType):
        """Player votes for the proposed team"""
        if self.phase != GamePhase.TEAM_VOTING:
            raise ValueError(f"Cannot vote for team in {self.phase.value} phase")
        
        if vote not in [VoteType.APPROVE, VoteType.REJECT]:
            raise ValueError("Team vote must be APPROVE or REJECT")
        
        current_quest = self.get_current_quest()
        current_quest.add_vote(player, vote)
        
        # Check if all players have voted
        if len(current_quest.pre_quest_votes) == self.player_count:
            self._process_team_votes()
    
    def _process_team_votes(self):
        """Process the team votes and move to the next phase"""
        current_quest = self.get_current_quest()
        approve_votes = sum(1 for vote in current_quest.pre_quest_votes.values() if vote == VoteType.APPROVE)
        
        if approve_votes > self.player_count / 2:
            # Team approved
            self.failed_votes_count = 0
            self.phase = GamePhase.QUEST
        else:
            # Team rejected
            self.failed_votes_count += 1
            current_quest.team_vote_counter += 1
            self.advance_leader()
            
            # Check if we've had 5 failed votes
            if self.failed_votes_count >= 5:
                # Evil wins if 5 consecutive team votes fail
                self.phase = GamePhase.GAME_END
                return
            
            self.phase = GamePhase.TEAM_BUILDING

    def _set_dummy_phase(self, phase: GamePhase):
        """Set a dummy phase for testing purposes"""
        self.phase = phase

    def vote_on_quest(self, player: Player, vote: VoteType):
        """Team member votes on the quest"""
        if self.phase != GamePhase.QUEST:
            raise ValueError(f"Cannot vote on quest in {self.phase.value} phase")
        
        if vote not in [VoteType.SUCCESS, VoteType.FAIL]:
            raise ValueError("Quest vote must be SUCCESS or FAIL")
        
        # Only evil players can fail quests
        if vote == VoteType.FAIL and player.team != Team.EVIL:
            raise ValueError("Good players cannot vote to fail quests")
        
        current_quest = self.get_current_quest()
        
        if player not in current_quest.team:
            raise ValueError("Only team members can vote on the quest")
        
        current_quest.add_vote(player, vote)
        
        # Check if all team members have voted
        if len(current_quest.in_quest_votes) == current_quest.required_team_size:
            # Process the result and immediately update quest counters
            result = current_quest.process_result()

            if result == QuestResult.SUCCESS:
                self.succeeded_quests += 1
            else:
                self.failed_quests += 1
                
            self._process_quest_result()

    
    def _process_quest_result(self):
        """Process the quest result and update game state"""
        # Check if the game is over
        if self.succeeded_quests >= 3:
            # If good team has won 3 quests, proceed to assassination
            self.phase = GamePhase.ASSASSINATION
        elif self.failed_quests >= 3:
            # If evil team has won 3 quests, evil wins
            self.phase = GamePhase.GAME_END
        else:
            # Move to the next quest
            self.current_quest_idx += 1
            self.advance_leader()
            self.phase = GamePhase.TEAM_BUILDING
    
    def assassinate(self, target: Player):
        """Assassin attempts to assassinate Merlin"""
        if self.phase != GamePhase.ASSASSINATION:
            raise ValueError(f"Cannot assassinate in {self.phase.value} phase")
        
        if not self.assassin:
            raise ValueError("No assassin in the game")
        
        self.assassinated_player = target
        self.phase = GamePhase.GAME_END
    
    def is_game_over(self) -> bool:
        """Check if the game is over"""
        return self.phase == GamePhase.GAME_END
    
    def get_winner(self) -> Optional[Team]:
        """Get the winner of the game"""
        if not self.is_game_over():
            return None
        
        if self.failed_quests >= 3:
            return Team.EVIL
        
        # If assassination phase happened
        if self.assassinated_player and self.assassinated_player.role == Role.MERLIN:
            return Team.EVIL
        
        return Team.GOOD
    
    def get_visible_roles(self, player: Player) -> Dict[Player, Role]:
        """Get roles visible to a specific player based on their own role"""
        visible_roles = {}
        
        # All players know their own role
        visible_roles[player] = player.role
        
        if player.role == Role.MERLIN:
            # Merlin sees all evil players except Mordred
            for p in self.players:
                if p.team == Team.EVIL and p.role != Role.MORDRED:
                    visible_roles[p] = Role.MINION  # Merlin only knows they're evil, not specific roles
        
        elif player.role == Role.PERCIVAL:
            # Percival sees Merlin and Morgana (but can't tell which is which)
            for p in self.players:
                if p.role in [Role.MERLIN, Role.MORGANA]:
                    visible_roles[p] = Role.MERLIN  # Percival sees both as Merlin
        
        elif player.team == Team.EVIL and player.role != Role.OBERON:
            # Evil players (except Oberon) see all other evil players (except Oberon)
            for p in self.players:
                if p.team == Team.EVIL and p.role != Role.OBERON and p != player:
                    visible_roles[p] = p.role
        
        return visible_roles
    
    def get_game_state(self, for_player: Optional[Player] = None):
        """
        Get the current game state
        
        Args:
            for_player: If provided, only return information visible to this player
        """
        state = {
            "phase": self.phase.value,  # Convert enum to string
            "current_quest_number": self.current_quest_idx + 1,
            "succeeded_quests": self.succeeded_quests,
            "failed_quests": self.failed_quests,
            "current_leader": self.get_current_leader().name,
            "failed_votes_count": self.failed_votes_count
        }
        
        if for_player:
            # Add information specific to this player
            state["role"] = for_player.role.value
            state["team"] = for_player.team.value
            state["visible_roles"] = {p.name: r.value for p, r in self.get_visible_roles(for_player).items()}
        else:
            # Full game state for spectators/logging
            state["players"] = {p.name: {"role": p.role.value, "team": p.team.value} for p in self.players}
        
        # Add current quest info
        current_quest = self.get_current_quest()
        state["current_quest"] = {
            "required_team_size": current_quest.required_team_size,
            "fails_required": current_quest.fails_required,
            "team": [p.name for p in current_quest.team] if current_quest.team else []
        }
        
        if self.phase == GamePhase.GAME_END:
            state["winner"] = self.get_winner().value if self.get_winner() else None
        
        return state