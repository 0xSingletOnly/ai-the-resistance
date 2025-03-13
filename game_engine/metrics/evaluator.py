from typing import Dict, List
from ..enums import Team, VoteType, QuestResult
from ..models import Player
from ..game import AvalonGame

class GameEvaluator:
    """Evaluates game performance metrics"""
    
    @staticmethod
    def evaluate_game(game: AvalonGame) -> Dict:
        """
        Evaluate a completed game and return metrics
        """
        metrics = {
            "team_metrics": GameEvaluator._calculate_team_metrics(game),
            "deception_metrics": GameEvaluator._calculate_deception_metrics(game)
        }
        return metrics

    @staticmethod
    def _calculate_team_metrics(game: AvalonGame) -> Dict:
        """Calculate win rate and success metrics for each team"""
        winner = game.get_winner()
        metrics = {
            "winner": winner.value,
            "good_team": {
                "quest_success_rate": game.succeeded_quests / (game.succeeded_quests + game.failed_quests),
                "won_game": winner == Team.GOOD
            },
            "evil_team": {
                "quest_failure_rate": game.failed_quests / (game.succeeded_quests + game.failed_quests),
                "won_game": winner == Team.EVIL
            }
        }
        return metrics

    @staticmethod
    def _calculate_deception_metrics(game: AvalonGame) -> Dict:
        """Calculate deception success metrics for evil team"""
        evil_players = [p for p in game.players if p.team == Team.EVIL]
        total_evil_quest_appearances = 0
        successful_deceptions = 0

        for player in evil_players:
            # Count times evil player was elected for quest
            quest_appearances = len(player.quest_vote_history)
            total_evil_quest_appearances += quest_appearances

            # Count successful deceptions (went on quest but didn't fail it)
            successful_deceptions += sum(
                1 for vote in player.quest_vote_history 
                if vote.vote == VoteType.SUCCESS
            )

        metrics = {
            "evil_team_quest_participation": total_evil_quest_appearances,
            "successful_deceptions": successful_deceptions,
            "deception_success_rate": successful_deceptions / total_evil_quest_appearances if total_evil_quest_appearances > 0 else 0
        }
        return metrics