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
    
    def test_evaluate_game_good_wins(self):
        """Test evaluation when good team wins."""
        # Simulate 3 successful quests and 1 failed quest
        self.game.succeeded_quests = 3
        self.game.failed_quests = 1
        self.game.phase = GamePhase.GAME_END
        
        # Add some quest vote history
        self.game.players[3].add_quest_vote(VoteType.SUCCESS, 1, ["Dave", "Alice"])  # Evil player deceiving
        self.game.players[4].add_quest_vote(VoteType.FAIL, 2, ["Eve", "Bob"])  # Evil player failing quest
        
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
        self.assertEqual(deception_metrics["deception_success_rate"], 0.5)
    
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
        self.assertEqual(deception_metrics["deception_success_rate"], 0)
    
    def test_no_quests_completed(self):
        """Test evaluation when no quests have been completed."""
        self.game.succeeded_quests = 0
        self.game.failed_quests = 0
        self.game.phase = GamePhase.TEAM_BUILDING
        
        metrics = GameEvaluator.evaluate_game(self.game)
        
        deception_metrics = metrics["deception_metrics"]
        self.assertEqual(deception_metrics["evil_team_quest_participation"], 0)
        self.assertEqual(deception_metrics["successful_deceptions"], 0)
        self.assertEqual(deception_metrics["deception_success_rate"], 0)