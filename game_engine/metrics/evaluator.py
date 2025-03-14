"""
Game performance metrics evaluator for The Resistance: Avalon.

This module provides functionality to analyze game outcomes and player behavior,
calculating various metrics that can be used to evaluate:
- Team performance (success rates in quests)
- Evil team deception effectiveness
- Player voting patterns and strategy
"""
from typing import Dict, List, Tuple
from ..enums import Team, VoteType, QuestResult
from ..models import Player
from ..game import AvalonGame

class GameEvaluator:
    """
    Evaluates game performance metrics for analysis and strategy insights.
    
    This class provides static methods to analyze various aspects of game play,
    including team success rates, deception effectiveness, and voting patterns.
    """
    
    @staticmethod
    def evaluate_game(game: AvalonGame) -> Dict:
        """
        Evaluate a completed game and return comprehensive metrics.
        
        Args:
            game: The completed game to evaluate
            
        Returns:
            Dictionary containing team and deception metrics
            
        Example return value:
        {
            "team_metrics": {
                "winner": "Good",
                "good_team": {
                    "quest_success_rate": 0.6,
                    "won_game": true
                },
                "evil_team": {
                    "quest_failure_rate": 0.4,
                    "won_game": false
                }
            },
            "deception_metrics": {
                "evil_team_quest_participation": 3,
                "successful_deceptions": 1,
                "deception_success_rate": 0.333
            }
        }
        """
        return {
            "team_metrics": GameEvaluator._calculate_team_metrics(game),
            "deception_metrics": GameEvaluator._calculate_deception_metrics(game),
            "voting_metrics": GameEvaluator._calculate_voting_metrics(game)
        }

    @staticmethod
    def _calculate_team_metrics(game: AvalonGame) -> Dict:
        """
        Calculate win rate and success metrics for each team.
        
        Args:
            game: The completed game to analyze
            
        Returns:
            Dictionary containing team performance metrics
        """
        winner = game.get_winner()
        total_quests = game.succeeded_quests + game.failed_quests
        
        if total_quests == 0:
            return {
                "winner": None,
                "good_team": {"quest_success_rate": 0.0, "won_game": False},
                "evil_team": {"quest_failure_rate": 0.0, "won_game": False}
            }
        
        return {
            "winner": getattr(winner, 'value', None),
            "good_team": {
                "quest_success_rate": game.succeeded_quests / total_quests,
                "won_game": winner == Team.GOOD
            },
            "evil_team": {
                "quest_failure_rate": game.failed_quests / total_quests,
                "won_game": winner == Team.EVIL
            }
        }

    @staticmethod
    def _calculate_deception_metrics(game: AvalonGame) -> Dict:
        """
        Calculate deception success metrics for evil team.
        
        Evaluates how effectively evil players:
        - Got selected for quests
        - Successfully deceived others (participated without failing)
        - Maintained cover through voting patterns
        
        Args:
            game: The completed game to analyze
            
        Returns:
            Dictionary containing deception effectiveness metrics
        """
        evil_players = [p for p in game.players if p.team == Team.EVIL]
        
        # Track evil player quest participation and success
        total_evil_appearances = 0
        successful_deceptions = 0
        failed_quest_votes = 0
        
        for player in evil_players:
            # Count times on quest
            quest_appearances = len(player.quest_vote_history)
            total_evil_appearances += quest_appearances
            
            # Count successful deceptions (went on quest but voted success)
            successful_deceptions += sum(
                1 for vote in player.quest_vote_history 
                if vote.vote == VoteType.SUCCESS
            )
            
            # Count failed quest votes
            failed_quest_votes += sum(
                1 for vote in player.quest_vote_history 
                if vote.vote == VoteType.FAIL
            )
        
        return {
            "evil_team_quest_participation": total_evil_appearances,
            "successful_deceptions": successful_deceptions,
            "failed_quest_votes": failed_quest_votes,
            "deception_success_rate": (
                successful_deceptions / total_evil_appearances 
                if total_evil_appearances > 0 else 0
            )
        }
    
    @staticmethod
    def _calculate_voting_metrics(game: AvalonGame) -> Dict:
        """
        Calculate voting pattern metrics for all players.
        
        Analyzes:
        - Team approval/rejection patterns
        - Correlation between team composition and votes
        - Voting alignment between players
        
        Args:
            game: The completed game to analyze
            
        Returns:
            Dictionary containing voting pattern metrics
        """
        team_vote_patterns = {}
        quest_vote_patterns = {}
        
        for player in game.players:
            # Calculate team voting patterns
            votes = player.get_voting_summary()
            team_vote_patterns[player.name] = {
                "approve_rate": (
                    votes["team_votes"]["approve"] / votes["team_votes"]["total"]
                    if votes["team_votes"]["total"] > 0 else 0
                ),
                "total_votes": votes["team_votes"]["total"]
            }
            
            # Calculate quest voting patterns for completed games
            if votes["quest_votes"]["total"] > 0:
                quest_vote_patterns[player.name] = {
                    "success_rate": (
                        votes["quest_votes"]["success"] / votes["quest_votes"]["total"]
                    ),
                    "total_votes": votes["quest_votes"]["total"]
                }
        
        return {
            "team_voting": team_vote_patterns,
            "quest_voting": quest_vote_patterns,
            "average_team_approve_rate": (
                sum(p["approve_rate"] for p in team_vote_patterns.values()) / 
                len(team_vote_patterns) if team_vote_patterns else 0
            )
        }