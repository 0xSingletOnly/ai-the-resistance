"""
Tests for the enums module of the Avalon game engine.
"""
import unittest
from game_engine.enums import Team, Role, GamePhase, QuestResult, VoteType


class TestEnums(unittest.TestCase):
    """Test cases for the game enumeration types."""
    
    def test_team_values(self):
        """Test that Team enum has the expected values."""
        self.assertEqual(Team.GOOD.value, "Good")
        self.assertEqual(Team.EVIL.value, "Evil")
    
    def test_role_values(self):
        """Test that Role enum has the expected values."""
        # Good team roles
        self.assertEqual(Role.MERLIN.value, "Merlin")
        self.assertEqual(Role.PERCIVAL.value, "Percival")
        self.assertEqual(Role.LOYAL_SERVANT.value, "Loyal Servant of Arthur")
        
        # Evil team roles
        self.assertEqual(Role.ASSASSIN.value, "Assassin")
        self.assertEqual(Role.MORGANA.value, "Morgana")
        self.assertEqual(Role.MORDRED.value, "Mordred")
        self.assertEqual(Role.OBERON.value, "Oberon")
        self.assertEqual(Role.MINION.value, "Minion of Mordred")
    
    def test_game_phase_values(self):
        """Test that GamePhase enum has the expected values."""
        self.assertEqual(GamePhase.SETUP.value, "Setup")
        self.assertEqual(GamePhase.TEAM_BUILDING.value, "Team Building")
        self.assertEqual(GamePhase.TEAM_VOTING.value, "Team Voting")
        self.assertEqual(GamePhase.QUEST.value, "Quest")
        self.assertEqual(GamePhase.ASSASSINATION.value, "Assassination")
        self.assertEqual(GamePhase.GAME_END.value, "Game End")
    
    def test_quest_result_values(self):
        """Test that QuestResult enum has the expected values."""
        self.assertEqual(QuestResult.SUCCESS.value, "Success")
        self.assertEqual(QuestResult.FAIL.value, "Fail")
        self.assertEqual(QuestResult.PENDING.value, "Pending")
        self.assertEqual(QuestResult.NOT_STARTED.value, "Not Started")
    
    def test_vote_type_values(self):
        """Test that VoteType enum has the expected values."""
        self.assertEqual(VoteType.APPROVE.value, "Approve")
        self.assertEqual(VoteType.REJECT.value, "Reject")
        self.assertEqual(VoteType.SUCCESS.value, "Success")
        self.assertEqual(VoteType.FAIL.value, "Fail")


if __name__ == "__main__":
    unittest.main()