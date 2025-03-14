"""
Tests for the game metrics evaluator module.
"""
import unittest
from game_engine.enums import Team, VoteType, GamePhase, Role
from game_engine.game import AvalonGame
from game_engine.metrics import GameEvaluator


class TestGameEvaluator(unittest.TestCase):
    """Test cases for the GameEvaluator class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a game with 5 players
        player_names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
        self.game = AvalonGame(player_names)
        
        # Set up known roles
        self.game.players[0].role = Role.MERLIN  # Alice
        self.game.players[1].role = Role.LOYAL_SERVANT  # Bob
        self.game.players[2].role = Role.LOYAL_SERVANT  # Charlie
        self.game.players[3].role = Role.ASSASSIN  # Dave
        self.game.players[4].role = Role.MINION  # Eve
        
        # Set teams
        self.game.players[0].team = Team.GOOD
        self.game.players[1].team = Team.GOOD
        self.game.players[2].team = Team.GOOD
        self.game.players[3].team = Team.EVIL
        self.game.players[4].team = Team.EVIL
    
    def test_evaluate_new_game(self):
        """Test evaluation of a newly started game."""
        metrics = GameEvaluator.evaluate_game(self.game)
        
        # Check team metrics for new game
        team_metrics = metrics["team_metrics"]
        self.assertIsNone(team_metrics["winner"])
        self.assertEqual(team_metrics["good_team"]["quest_success_rate"], 0.0)
        self.assertEqual(team_metrics["evil_team"]["quest_failure_rate"], 0.0)
        self.assertFalse(team_metrics["good_team"]["won_game"])
        self.assertFalse(team_metrics["evil_team"]["won_game"])
        
        # Check deception metrics for new game
        deception_metrics = metrics["deception_metrics"]
        self.assertEqual(deception_metrics["evil_team_quest_participation"], 0)
        self.assertEqual(deception_metrics["successful_deceptions"], 0)
        self.assertEqual(deception_metrics["failed_quest_votes"], 0)
        self.assertEqual(deception_metrics["deception_success_rate"], 0)
        
        # Check voting metrics for new game
        voting_metrics = metrics["voting_metrics"]
        self.assertEqual(voting_metrics["average_team_approve_rate"], 0)
        self.assertEqual(len(voting_metrics["team_voting"]), 5)
        self.assertEqual(len(voting_metrics["quest_voting"]), 0)
    
    def test_evaluate_game_good_wins(self):
        """Test evaluation when good team wins."""
        # Simulate 3 successful quests and 1 failed quest
        self.game.succeeded_quests = 3
        self.game.failed_quests = 1
        self.game.phase = GamePhase.GAME_END
        
        # Add some quest vote history
        self.game.players[3].add_quest_vote(VoteType.SUCCESS, 1, ["Dave", "Alice"])  # Evil player deceiving
        self.game.players[4].add_quest_vote(VoteType.FAIL, 2, ["Eve", "Bob"])  # Evil player failing quest
        
        # Add some team vote history
        for player in self.game.players:
            player.add_team_vote(VoteType.APPROVE, 1, "Alice", ["Dave", "Alice"])
            player.add_team_vote(VoteType.REJECT, 2, "Bob", ["Eve", "Bob"])
        
        metrics = GameEvaluator.evaluate_game(self.game)
        
        # Check team metrics
        team_metrics = metrics["team_metrics"]
        self.assertEqual(team_metrics["winner"], Team.GOOD.value)
        self.assertEqual(team_metrics["good_team"]["quest_success_rate"], 0.75)
        self.assertTrue(team_metrics["good_team"]["won_game"])
        self.assertEqual(team_metrics["evil_team"]["quest_failure_rate"], 0.25)
        self.assertFalse(team_metrics["evil_team"]["won_game"])
        
        # Check deception metrics
        deception_metrics = metrics["deception_metrics"]
        self.assertEqual(deception_metrics["evil_team_quest_participation"], 2)
        self.assertEqual(deception_metrics["successful_deceptions"], 1)
        self.assertEqual(deception_metrics["failed_quest_votes"], 1)
        self.assertEqual(deception_metrics["deception_success_rate"], 0.5)
        
        # Check voting metrics
        voting_metrics = metrics["voting_metrics"]
        self.assertEqual(voting_metrics["average_team_approve_rate"], 0.5)  # Each player approved 1/2 teams
        self.assertEqual(len(voting_metrics["team_voting"]), 5)
        self.assertEqual(len(voting_metrics["quest_voting"]), 2)  # Only 2 players went on quests
    
    def test_evaluate_game_evil_wins(self):
        """Test evaluation when evil team wins."""
        # Simulate 2 successful quests and 3 failed quests
        self.game.succeeded_quests = 2
        self.game.failed_quests = 3
        self.game.phase = GamePhase.GAME_END
        
        # Add some quest vote history
        self.game.players[3].add_quest_vote(VoteType.FAIL, 1, ["Dave", "Alice"])
        self.game.players[4].add_quest_vote(VoteType.FAIL, 2, ["Eve", "Bob"])
        self.game.players[3].add_quest_vote(VoteType.FAIL, 3, ["Dave", "Charlie"])
        
        # Add some team vote history - more rejections from evil team
        for player in self.game.players:
            if player.team == Team.EVIL:
                player.add_team_vote(VoteType.REJECT, 1, "Alice", ["Bob", "Charlie"])
                player.add_team_vote(VoteType.APPROVE, 2, "Dave", ["Dave", "Eve"])
            else:
                player.add_team_vote(VoteType.APPROVE, 1, "Alice", ["Bob", "Charlie"])
                player.add_team_vote(VoteType.REJECT, 2, "Dave", ["Dave", "Eve"])
        
        metrics = GameEvaluator.evaluate_game(self.game)
        
        # Check team metrics
        team_metrics = metrics["team_metrics"]
        self.assertEqual(team_metrics["winner"], Team.EVIL.value)
        self.assertEqual(team_metrics["good_team"]["quest_success_rate"], 0.4)
        self.assertFalse(team_metrics["good_team"]["won_game"])
        self.assertEqual(team_metrics["evil_team"]["quest_failure_rate"], 0.6)
        self.assertTrue(team_metrics["evil_team"]["won_game"])
        
        # Check deception metrics
        deception_metrics = metrics["deception_metrics"]
        self.assertEqual(deception_metrics["evil_team_quest_participation"], 3)
        self.assertEqual(deception_metrics["successful_deceptions"], 0)
        self.assertEqual(deception_metrics["failed_quest_votes"], 3)
        self.assertEqual(deception_metrics["deception_success_rate"], 0)
        
        # Check voting metrics
        voting_metrics = metrics["voting_metrics"]
        self.assertEqual(voting_metrics["average_team_approve_rate"], 0.5)
        
        # Check evil team voting patterns
        dave_voting = voting_metrics["team_voting"]["Dave"]
        eve_voting = voting_metrics["team_voting"]["Eve"]
        self.assertEqual(dave_voting["approve_rate"], 0.5)
        self.assertEqual(eve_voting["approve_rate"], 0.5)
        
        # Check quest voting patterns
        dave_quests = voting_metrics["quest_voting"]["Dave"]
        eve_quests = voting_metrics["quest_voting"]["Eve"]
        self.assertEqual(dave_quests["success_rate"], 0.0)  # All fails
        self.assertEqual(eve_quests["success_rate"], 0.0)  # All fails
    
    def test_voting_pattern_analysis(self):
        """Test detailed voting pattern analysis."""
        # Add varied voting patterns
        # Good players tend to approve good teams
        for good_player in [self.game.players[i] for i in range(3)]:
            good_player.add_team_vote(VoteType.APPROVE, 1, "Alice", ["Alice", "Bob"])  # Good team
            good_player.add_team_vote(VoteType.REJECT, 2, "Dave", ["Dave", "Eve"])    # Evil team
            good_player.add_team_vote(VoteType.APPROVE, 3, "Bob", ["Bob", "Charlie"]) # Good team
        
        # Evil players show different patterns
        for evil_player in [self.game.players[i] for i in [3, 4]]:
            evil_player.add_team_vote(VoteType.REJECT, 1, "Alice", ["Alice", "Bob"])
            evil_player.add_team_vote(VoteType.APPROVE, 2, "Dave", ["Dave", "Eve"])
            evil_player.add_team_vote(VoteType.REJECT, 3, "Bob", ["Bob", "Charlie"])
        
        # Add some quest votes
        self.game.players[0].add_quest_vote(VoteType.SUCCESS, 1, ["Alice", "Bob"])
        self.game.players[1].add_quest_vote(VoteType.SUCCESS, 1, ["Alice", "Bob"])
        self.game.players[3].add_quest_vote(VoteType.SUCCESS, 2, ["Dave", "Eve"])  # Deception
        self.game.players[4].add_quest_vote(VoteType.FAIL, 2, ["Dave", "Eve"])
        
        metrics = GameEvaluator.evaluate_game(self.game)
        voting_metrics = metrics["voting_metrics"]
        
        # Check team voting patterns
        self.assertGreater(
            voting_metrics["team_voting"]["Alice"]["approve_rate"],
            voting_metrics["team_voting"]["Dave"]["approve_rate"]
        )
        
        # Check quest voting patterns
        self.assertEqual(voting_metrics["quest_voting"]["Alice"]["success_rate"], 1.0)
        self.assertEqual(voting_metrics["quest_voting"]["Dave"]["success_rate"], 1.0)  # Deceptive success
        self.assertEqual(voting_metrics["quest_voting"]["Eve"]["success_rate"], 0.0)   # Failed quest


if __name__ == "__main__":
    unittest.main()