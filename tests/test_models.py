"""
Tests for the models module of the Avalon game engine.
"""
import unittest
from typing import List
from game_engine.enums import Role, Team, VoteType, QuestResult
from game_engine.models import Player, Quest, TeamVoteRecord, QuestVoteRecord


class TestVoteRecords(unittest.TestCase):
    """Test cases for the vote record data classes."""
    
    def test_team_vote_record_immutable(self):
        """Test that TeamVoteRecord is immutable."""
        record = TeamVoteRecord(
            quest_number=1,
            leader="Alice",
            proposed_team=["Alice", "Bob"],
            vote=VoteType.APPROVE
        )
        with self.assertRaises(AttributeError):
            record.vote = VoteType.REJECT
    
    def test_quest_vote_record_immutable(self):
        """Test that QuestVoteRecord is immutable."""
        record = QuestVoteRecord(
            quest_number=1,
            team=["Alice", "Bob"],
            vote=VoteType.SUCCESS
        )
        with self.assertRaises(AttributeError):
            record.vote = VoteType.FAIL


class TestPlayer(unittest.TestCase):
    """Test cases for the Player class."""
    
    def test_player_initialization_validation(self):
        """Test player initialization with invalid inputs."""
        with self.assertRaises(ValueError):
            Player("")  # Empty name
        with self.assertRaises(ValueError):
            Player(None)  # None name
        with self.assertRaises(ValueError):
            Player(123)  # Non-string name
    
    def test_player_initialization(self):
        """Test valid player initialization."""
        player = Player("Alice")
        self.assertEqual(player.name, "Alice")
        self.assertIsNone(player.role)
        self.assertIsNone(player.team)
        self.assertEqual(player.team_vote_history, [])
        self.assertEqual(player.quest_vote_history, [])
    
    def test_assign_role_validation(self):
        """Test role assignment validation."""
        player = Player("Bob")
        
        # Test invalid role type
        with self.assertRaises(ValueError):
            player.assign_role("MERLIN")  # String instead of Role enum
        
        # Test reassignment
        player.assign_role(Role.MERLIN)
        with self.assertRaises(ValueError):
            player.assign_role(Role.ASSASSIN)
    
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
    
    def test_add_team_vote(self):
        """Test adding team votes to player history."""
        player = Player("Alice")
        player.assign_role(Role.MERLIN)
        
        # Add some team votes
        player.add_team_vote(
            vote=VoteType.APPROVE,
            quest_number=1,
            leader="Bob",
            proposed_team=["Bob", "Alice", "Charlie"]
        )
        player.add_team_vote(
            vote=VoteType.REJECT,
            quest_number=1,
            leader="Charlie",
            proposed_team=["Charlie", "Dave", "Eve"]
        )
        
        # Check voting history
        self.assertEqual(len(player.team_vote_history), 2)
        self.assertEqual(player.team_vote_history[0].vote, VoteType.APPROVE)
        self.assertEqual(player.team_vote_history[0].leader, "Bob")
        self.assertEqual(player.team_vote_history[1].vote, VoteType.REJECT)
        self.assertEqual(player.team_vote_history[1].leader, "Charlie")
    
    def test_add_quest_vote(self):
        """Test adding quest votes to player history."""
        player = Player("Bob")
        player.assign_role(Role.ASSASSIN)
        
        # Add some quest votes
        player.add_quest_vote(
            vote=VoteType.SUCCESS,
            quest_number=1,
            team=["Alice", "Bob", "Charlie"]
        )
        player.add_quest_vote(
            vote=VoteType.FAIL,
            quest_number=2,
            team=["Bob", "Dave", "Eve"]
        )
        
        # Check voting history
        self.assertEqual(len(player.quest_vote_history), 2)
        self.assertEqual(player.quest_vote_history[0].vote, VoteType.SUCCESS)
        self.assertEqual(player.quest_vote_history[0].team, ["Alice", "Bob", "Charlie"])
        self.assertEqual(player.quest_vote_history[1].vote, VoteType.FAIL)
        self.assertEqual(player.quest_vote_history[1].team, ["Bob", "Dave", "Eve"])
    
    def test_invalid_team_vote(self):
        """Test that invalid team votes are rejected."""
        player = Player("Charlie")
        
        # Try to add invalid vote types
        with self.assertRaises(ValueError):
            player.add_team_vote(
                vote=VoteType.SUCCESS,  # Invalid vote type for team vote
                quest_number=1,
                leader="Bob",
                proposed_team=["Bob", "Alice", "Charlie"]
            )
        with self.assertRaises(ValueError):
            player.add_team_vote(
                vote=VoteType.FAIL,  # Invalid vote type for team vote
                quest_number=1,
                leader="Bob",
                proposed_team=["Bob", "Alice", "Charlie"]
            )
            
        # Check that no votes were recorded
        self.assertEqual(len(player.team_vote_history), 0)
    
    def test_invalid_quest_vote(self):
        """Test that invalid quest votes are rejected."""
        player = Player("Dave")
        
        # Try to add invalid vote types
        with self.assertRaises(ValueError):
            player.add_quest_vote(
                vote=VoteType.APPROVE,  # Invalid vote type for quest vote
                quest_number=1,
                team=["Bob", "Dave", "Eve"]
            )
        with self.assertRaises(ValueError):
            player.add_quest_vote(
                vote=VoteType.REJECT,  # Invalid vote type for quest vote
                quest_number=1,
                team=["Bob", "Dave", "Eve"]
            )
            
        # Check that no votes were recorded
        self.assertEqual(len(player.quest_vote_history), 0)
    
    def test_team_vote_history(self):
        """Test team vote history tracking with context"""
        player = Player("Alice")
        player.assign_role(Role.MERLIN)
        
        # Test a team vote with context
        player.add_team_vote(
            vote=VoteType.APPROVE,
            quest_number=1,
            leader="Bob",
            proposed_team=["Bob", "Alice", "Charlie"]
        )
        
        # Check the recorded vote
        self.assertEqual(len(player.team_vote_history), 1)
        record = player.team_vote_history[0]
        self.assertEqual(record.quest_number, 1)
        self.assertEqual(record.leader, "Bob")
        self.assertEqual(record.proposed_team, ["Bob", "Alice", "Charlie"])
        self.assertEqual(record.vote, VoteType.APPROVE)
    
    def test_quest_vote_history(self):
        """Test quest vote history tracking with context"""
        player = Player("Alice")
        player.assign_role(Role.MERLIN)
        
        # Test a quest vote with context
        player.add_quest_vote(
            vote=VoteType.SUCCESS,
            quest_number=1,
            team=["Alice", "Bob", "Charlie"]
        )
        
        # Check the recorded vote
        self.assertEqual(len(player.quest_vote_history), 1)
        record = player.quest_vote_history[0]
        self.assertEqual(record.quest_number, 1)
        self.assertEqual(record.team, ["Alice", "Bob", "Charlie"])
        self.assertEqual(record.vote, VoteType.SUCCESS)
    
    def test_add_team_vote_validation(self):
        """Test team vote validation."""
        player = Player("Charlie")
        
        # Test invalid vote type
        with self.assertRaises(ValueError):
            player.add_team_vote(
                vote=VoteType.SUCCESS,  # Invalid for team vote
                quest_number=1,
                leader="Bob",
                proposed_team=["Bob", "Charlie"]
            )
        
        # Test invalid quest number
        with self.assertRaises(ValueError):
            player.add_team_vote(
                vote=VoteType.APPROVE,
                quest_number=0,  # Invalid quest number
                leader="Bob",
                proposed_team=["Bob", "Charlie"]
            )
    
    def test_add_quest_vote_validation(self):
        """Test quest vote validation."""
        player = Player("Dave")
        
        # Test invalid vote type
        with self.assertRaises(ValueError):
            player.add_quest_vote(
                vote=VoteType.APPROVE,  # Invalid for quest vote
                quest_number=1,
                team=["Bob", "Dave"]
            )
        
        # Test invalid quest number
        with self.assertRaises(ValueError):
            player.add_quest_vote(
                vote=VoteType.SUCCESS,
                quest_number=-1,  # Invalid quest number
                team=["Bob", "Dave"]
            )
    
    def test_voting_summary(self):
        """Test voting summary generation."""
        player = Player("Eve")
        
        # Add some team votes
        player.add_team_vote(VoteType.APPROVE, 1, "Alice", ["Alice", "Eve"])
        player.add_team_vote(VoteType.REJECT, 1, "Bob", ["Bob", "Charlie"])
        player.add_team_vote(VoteType.APPROVE, 2, "Dave", ["Dave", "Eve"])
        
        # Add some quest votes
        player.add_quest_vote(VoteType.SUCCESS, 1, ["Alice", "Eve"])
        player.add_quest_vote(VoteType.FAIL, 2, ["Dave", "Eve"])
        
        summary = player.get_voting_summary()
        self.assertEqual(summary["team_votes"]["approve"], 2)
        self.assertEqual(summary["team_votes"]["reject"], 1)
        self.assertEqual(summary["team_votes"]["total"], 3)
        self.assertEqual(summary["quest_votes"]["success"], 1)
        self.assertEqual(summary["quest_votes"]["fail"], 1)
        self.assertEqual(summary["quest_votes"]["total"], 2)
    
    def test_player_equality(self):
        """Test player equality and hashing."""
        player1 = Player("Frank")
        player2 = Player("Frank")
        player3 = Player("Grace")
        
        self.assertEqual(player1, player2)
        self.assertNotEqual(player1, player3)
        self.assertEqual(hash(player1), hash(player2))
        self.assertNotEqual(hash(player1), hash(player3))


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
    
    def test_quest_initialization_validation(self):
        """Test quest initialization with invalid parameters."""
        with self.assertRaises(ValueError):
            Quest(0, 3, 1)  # Invalid quest number
        with self.assertRaises(ValueError):
            Quest(1, 0, 1)  # Invalid team size
        with self.assertRaises(ValueError):
            Quest(1, 3, 0)  # Invalid fails required
        with self.assertRaises(ValueError):
            Quest(1, 3, 4)  # Fails required > team size
    
    def test_set_team_validation(self):
        """Test team setting validation."""
        # Test wrong team size
        with self.assertRaises(ValueError):
            self.quest.set_team(self.team_members[:2], self.leader)
        
        # Test duplicate players
        duplicate_team = [self.team_members[0], self.team_members[0], self.team_members[1]]
        with self.assertRaises(ValueError):
            self.quest.set_team(duplicate_team, self.leader)
    
    def test_vote_processing_validation(self):
        """Test vote processing validation."""
        self.quest.set_team(self.team_members, self.leader)
        
        # Try to process result before all votes are in
        self.quest.add_vote(self.team_members[0], VoteType.SUCCESS)
        self.quest.add_vote(self.team_members[1], VoteType.SUCCESS)
        
        with self.assertRaises(ValueError):
            self.quest.process_result()
    
    def test_quest_string_representation(self):
        """Test quest string representation."""
        quest = Quest(1, 3, 1)
        self.assertIn("Not Started", str(quest))
        
        # After setting team
        quest.set_team(self.team_members, self.leader)
        self.assertIn("Team Proposed", str(quest))
        
        # After completion
        for player in self.team_members:
            quest.add_vote(player, VoteType.SUCCESS)
        quest.process_result()
        self.assertIn("Complete - Success", str(quest))


if __name__ == "__main__":
    unittest.main()