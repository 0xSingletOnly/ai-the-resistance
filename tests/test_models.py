"""
Tests for the models module of the Avalon game engine.
"""
import unittest
from game_engine.enums import Role, Team, VoteType, QuestResult
from game_engine.models import Player, Quest


class TestPlayer(unittest.TestCase):
    """Test cases for the Player class."""
    
    def test_player_initialization(self):
        """Test player initialization."""
        player = Player("Alice")
        self.assertEqual(player.name, "Alice")
        self.assertIsNone(player.role)
        self.assertIsNone(player.team)
    
    def test_assign_good_role(self):
        """Test assigning a good role to a player."""
        player = Player("Bob")
        player.assign_role(Role.MERLIN)
        self.assertEqual(player.role, Role.MERLIN)
        self.assertEqual(player.team, Team.GOOD)
        
        player = Player("Charlie")
        player.assign_role(Role.PERCIVAL)
        self.assertEqual(player.role, Role.PERCIVAL)
        self.assertEqual(player.team, Team.GOOD)
        
        player = Player("Dave")
        player.assign_role(Role.LOYAL_SERVANT)
        self.assertEqual(player.role, Role.LOYAL_SERVANT)
        self.assertEqual(player.team, Team.GOOD)
    
    def test_assign_evil_role(self):
        """Test assigning an evil role to a player."""
        player = Player("Eve")
        player.assign_role(Role.ASSASSIN)
        self.assertEqual(player.role, Role.ASSASSIN)
        self.assertEqual(player.team, Team.EVIL)
        
        player = Player("Frank")
        player.assign_role(Role.MORGANA)
        self.assertEqual(player.role, Role.MORGANA)
        self.assertEqual(player.team, Team.EVIL)
        
        player = Player("Grace")
        player.assign_role(Role.MORDRED)
        self.assertEqual(player.role, Role.MORDRED)
        self.assertEqual(player.team, Team.EVIL)
        
        player = Player("Hank")
        player.assign_role(Role.OBERON)
        self.assertEqual(player.role, Role.OBERON)
        self.assertEqual(player.team, Team.EVIL)
        
        player = Player("Ivy")
        player.assign_role(Role.MINION)
        self.assertEqual(player.role, Role.MINION)
        self.assertEqual(player.team, Team.EVIL)


class TestQuest(unittest.TestCase):
    """Test cases for the Quest class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.quest = Quest(1, 3, 1)
        self.leader = Player("Leader")
        self.leader.assign_role(Role.LOYAL_SERVANT)
        
        self.team_members = []
        for i in range(3):
            player = Player(f"Player{i}")
            player.assign_role(Role.LOYAL_SERVANT if i < 2 else Role.MINION)
            self.team_members.append(player)
    
    def test_quest_initialization(self):
        """Test quest initialization."""
        self.assertEqual(self.quest.quest_number, 1)
        self.assertEqual(self.quest.required_team_size, 3)
        self.assertEqual(self.quest.fails_required, 1)
        self.assertEqual(self.quest.team, [])
        self.assertEqual(self.quest.pre_quest_votes, {})
        self.assertEqual(self.quest.in_quest_votes, {})
        self.assertEqual(self.quest.result, QuestResult.NOT_STARTED)
        self.assertIsNone(self.quest.leader)
        self.assertEqual(self.quest.team_vote_counter, 0)
    
    def test_set_team(self):
        """Test setting a team for a quest."""
        self.quest.set_team(self.team_members, self.leader)
        self.assertEqual(self.quest.team, self.team_members)
        self.assertEqual(self.quest.leader, self.leader)
        self.assertEqual(self.quest.in_quest_votes, {})
    
    def test_set_team_wrong_size(self):
        """Test that setting a team with wrong size raises an error."""
        with self.assertRaises(ValueError):
            self.quest.set_team(self.team_members[:2], self.leader)
    
    def test_add_vote(self):
        """Test adding votes to a quest."""
        self.quest.set_team(self.team_members, self.leader)
        
        # Team members can vote on quest success/failure
        for i, player in enumerate(self.team_members):
            vote = VoteType.SUCCESS if i < 2 else VoteType.FAIL
            self.quest.add_vote(player, vote)
            self.assertEqual(self.quest.in_quest_votes[player], vote)
    
    def test_add_vote_non_team_member(self):
        """Test that non-team members cannot vote on quest success."""
        self.quest.set_team(self.team_members, self.leader)
        non_team_member = Player("Outsider")
        non_team_member.assign_role(Role.LOYAL_SERVANT)
        
        with self.assertRaises(ValueError):
            self.quest.add_vote(non_team_member, VoteType.SUCCESS)
    
    def test_process_result_success(self):
        """Test processing quest results for success."""
        self.quest.set_team(self.team_members, self.leader)
        
        # All votes are SUCCESS
        for player in self.team_members:
            self.quest.add_vote(player, VoteType.SUCCESS)
        
        result = self.quest.process_result()
        self.assertEqual(result, QuestResult.SUCCESS)
        self.assertEqual(self.quest.result, QuestResult.SUCCESS)
    
    def test_process_result_fail_with_one_fail(self):
        """Test processing quest results with one fail vote."""
        self.quest.set_team(self.team_members, self.leader)
        
        # Two SUCCESS votes, one FAIL vote
        for i, player in enumerate(self.team_members):
            vote = VoteType.SUCCESS if i < 2 else VoteType.FAIL
            self.quest.add_vote(player, vote)
        
        result = self.quest.process_result()
        self.assertEqual(result, QuestResult.FAIL)
        self.assertEqual(self.quest.result, QuestResult.FAIL)
    
    def test_process_result_with_two_fails_required(self):
        """Test processing quest results with two fails required."""
        quest = Quest(4, 4, 2)  # 4th quest with 4 team members, requires 2 fails
        leader = Player("Leader")
        leader.assign_role(Role.LOYAL_SERVANT)
        
        team_members = []
        for i in range(4):
            player = Player(f"Player{i}")
            # First 2 are good, last 2 are evil
            player.assign_role(Role.LOYAL_SERVANT if i < 2 else Role.MINION)
            team_members.append(player)
        
        quest.set_team(team_members, leader)
        
        # 2 SUCCESS votes, 2 FAIL votes
        for i, player in enumerate(team_members):
            vote = VoteType.SUCCESS if i < 2 else VoteType.FAIL
            quest.add_vote(player, vote)
        
        result = quest.process_result()
        self.assertEqual(result, QuestResult.FAIL)
        
        # Now try with only 1 FAIL vote
        quest = Quest(4, 4, 2)
        quest.set_team(team_members, leader)
        
        # 3 SUCCESS votes, 1 FAIL vote
        for i, player in enumerate(team_members):
            vote = VoteType.SUCCESS if i < 3 else VoteType.FAIL
            quest.add_vote(player, vote)
        
        result = quest.process_result()
        self.assertEqual(result, QuestResult.SUCCESS)  # Only 1 fail, but 2 required to fail


if __name__ == "__main__":
    unittest.main()