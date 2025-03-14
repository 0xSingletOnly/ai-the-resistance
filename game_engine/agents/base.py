"""
Base agent interface and implementations for The Resistance: Avalon.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import random
from ..enums import Team, Role, VoteType, QuestResult
from ..models import Player, Quest
from ..game import AvalonGame

class AvalonAgent(ABC):
    """Base interface for all Avalon agents."""
    
    def __init__(self, player: Player):
        self.player = player
    
    @abstractmethod
    def propose_team(self, game: AvalonGame) -> List[Player]:
        """Decide which players to include in a quest team."""
        pass
    
    @abstractmethod
    def vote_for_team(self, game: AvalonGame, proposed_team: List[Player]) -> VoteType:
        """Vote on whether to approve or reject a proposed team."""
        pass
    
    @abstractmethod
    def vote_on_quest(self, game: AvalonGame) -> VoteType:
        """Vote on the outcome of a quest (SUCCESS/FAIL)."""
        pass
    
    @abstractmethod
    def choose_assassination_target(self, game: AvalonGame) -> Player:
        """Choose which player to assassinate (Assassin only)."""
        pass

class RuleBasedAgent(AvalonAgent):
    """Rule-based agent that uses predefined strategies."""
    
    def propose_team(self, game: AvalonGame) -> List[Player]:
        """
        Simple team proposal strategy:
        - Good players try to maximize good players on team
        - Evil players try to include at least one evil player
        """
        quest = game.get_current_quest()
        team_size = quest.required_team_size
        candidates = [p for p in game.players if p != self.player]  # All players except self
        team = [self.player]  # Always include self
        remaining_size = team_size - 1
        
        if self.player.team == Team.GOOD:
            # Good players prefer other players they know are good
            visible_roles = game.get_visible_roles(self.player)
            known_good = [p for p in candidates if 
                         p in visible_roles and 
                         visible_roles[p] in [Role.MERLIN, Role.PERCIVAL, Role.LOYAL_SERVANT]]
            
            # Add known good players first
            team.extend(known_good[:remaining_size])
            remaining_size -= len(team) - 1  # Subtract 1 to account for self
            
            if remaining_size > 0:
                # Fill remaining slots with random players not already in team
                remaining = [p for p in candidates if p not in team]
                team.extend(random.sample(remaining, remaining_size))
        else:
            # Evil players try to include at least one evil teammate
            visible_roles = game.get_visible_roles(self.player)
            known_evil = [p for p in candidates if 
                         p in visible_roles and 
                         visible_roles[p] in [Role.ASSASSIN, Role.MORGANA, Role.MINION]]
            
            # Add one evil teammate if possible
            if known_evil and remaining_size > 0:
                team.append(random.choice(known_evil))
                remaining_size -= 1
            
            if remaining_size > 0:
                # Fill remaining slots with random players not already in team
                remaining = [p for p in candidates if p not in team]
                team.extend(random.sample(remaining, remaining_size))
        
        return team  # No need to slice, we've built exactly the right size
    
    def vote_for_team(self, game: AvalonGame, proposed_team: List[Player]) -> VoteType:
        """
        Simple team voting strategy:
        - Good players approve teams unless they see evil players
        - Evil players approve teams with evil players or when rejections are high
        """
        visible_roles = game.get_visible_roles(self.player)
        
        if self.player.team == Team.GOOD:
            # Reject only if we can see evil players on the team
            known_evil = sum(1 for p in proposed_team 
                           if p in visible_roles and 
                           visible_roles[p] in [Role.ASSASSIN, Role.MORGANA, Role.MINION])
            return VoteType.REJECT if known_evil > 0 else VoteType.APPROVE
        else:
            # Evil players are more likely to approve teams:
            # - When they see other evil players
            # - When there have been many rejections (to avoid losing by rejection)
            has_evil = any(p in visible_roles and 
                          visible_roles[p] in [Role.ASSASSIN, Role.MORGANA, Role.MINION] 
                          for p in proposed_team)
            
            # More likely to approve as failed votes increase
            approve_probability = 0.3  # Base probability
            if has_evil:
                approve_probability += 0.4  # Much more likely if evil players present
            approve_probability += game.failed_votes_count * 0.1  # More likely as rejections increase
            
            return VoteType.APPROVE if random.random() < approve_probability else VoteType.REJECT
    
    def vote_on_quest(self, game: AvalonGame) -> VoteType:
        """
        Simple quest voting strategy:
        - Good players always vote SUCCESS
        - Evil players sometimes vote FAIL based on game state
        """
        if self.player.team == Team.GOOD:
            return VoteType.SUCCESS
        else:
            # Evil players are more likely to fail later quests
            quest_idx = game.current_quest_idx
            fail_probability = 0.5 + (quest_idx * 0.1)  # Increases with each quest
            return VoteType.FAIL if random.random() < fail_probability else VoteType.SUCCESS
    
    def choose_assassination_target(self, game: AvalonGame) -> Player:
        """
        Simple assassination strategy:
        - Target players who consistently approved successful quests
        """
        if self.player.role != Role.ASSASSIN:
            raise ValueError("Only the Assassin can choose assassination targets")
        
        # Score players based on their voting patterns
        player_scores = {p: 0 for p in game.players if p != self.player}
        
        for quest in game.quests:
            if quest.result:  # Only consider completed quests
                for player, vote in quest.pre_quest_votes.items():
                    if vote == VoteType.APPROVE and quest.result == QuestResult.SUCCESS:
                        player_scores[player] += 1
        
        # Return the player with the highest score
        return max(player_scores.items(), key=lambda x: x[1])[0]
