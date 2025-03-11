"""
Tests for the game module of the Avalon game engine.
"""
import unittest
from unittest.mock import patch
from game_engine.enums import Team, Role, GamePhase, QuestResult, VoteType
from game_engine.models import Player, Quest
from game_engine.game import AvalonGame


class TestAvalonGameBasics(unittest.TestCase):
    """Test basic initialization and properties of the AvalonGame class."""
    
    def test_game_initialization(self):
        """Test game initialization with default roles."""
        player_names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
        game = AvalonGame(player_names)
        
        # Check player count and player objects
        self.assertEqual(game.player_count, 5)
        self.assertEqual(len(game.players), 5)
        for i, name in enumerate(player_names):
            self.assertEqual(game.players[i].name, name)
        
        # Check initial game state
        self.assertEqual(game.current_quest_idx, 0)
        self.assertEqual(game.succeeded_quests, 0)
        self.assertEqual(game.failed_quests, 0)
        self.assertEqual(game.phase, GamePhase.SETUP)
        self.assertIsNotNone(game.assassin)  # An assassin should be assigned
    
    def test_invalid_player_count(self):
        """Test game initialization with invalid player count."""
        # Too few players
        with self.assertRaises(ValueError):
            AvalonGame(["Alice", "Bob", "Charlie", "Dave"])
        
        # Too many players
        with self.assertRaises(ValueError):
            AvalonGame(["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10", "P11"])
    
    def test_role_assignment(self):
        """Test that roles are properly assigned."""
        player_names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
        game = AvalonGame(player_names)
        
        # Check that all players have roles and teams
        for player in game.players:
            self.assertIsNotNone(player.role)
            self.assertIsNotNone(player.team)
        
        # Check team balance for 5 players: should be 3 good, 2 evil
        good_count = sum(1 for player in game.players if player.team == Team.GOOD)
        evil_count = sum(1 for player in game.players if player.team == Team.EVIL)
        self.assertEqual(good_count, 3)
        self.assertEqual(evil_count, 2)
        
        # Check required roles: Merlin and Assassin
        has_merlin = any(player.role == Role.MERLIN for player in game.players)
        has_assassin = any(player.role == Role.ASSASSIN for player in game.players)
        self.assertTrue(has_merlin)
        self.assertTrue(has_assassin)
    
    def test_custom_roles(self):
        """Test game initialization with custom roles."""
        player_names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
        custom_roles = {
            Role.MERLIN: 1,
            Role.PERCIVAL: 1,
            Role.LOYAL_SERVANT: 1,
            Role.ASSASSIN: 1,
            Role.MORGANA: 1
        }
        game = AvalonGame(player_names, custom_roles)
        
        # Check that all roles were assigned as expected
        role_counts = {}
        for player in game.players:
            if player.role not in role_counts:
                role_counts[player.role] = 0
            role_counts[player.role] += 1
        
        self.assertEqual(role_counts[Role.MERLIN], 1)
        self.assertEqual(role_counts[Role.PERCIVAL], 1)
        self.assertEqual(role_counts[Role.LOYAL_SERVANT], 1)
        self.assertEqual(role_counts[Role.ASSASSIN], 1)
        self.assertEqual(role_counts[Role.MORGANA], 1)
    
    def test_invalid_custom_roles(self):
        """Test that invalid custom role configurations are rejected."""
        player_names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
        
        # Too many good roles
        custom_roles = {
            Role.MERLIN: 1,
            Role.PERCIVAL: 1,
            Role.LOYAL_SERVANT: 2,  # This gives 4 good roles, should be 3
            Role.ASSASSIN: 1
        }
        with self.assertRaises(ValueError):
            AvalonGame(player_names, custom_roles)
        
        # Too many evil roles
        custom_roles = {
            Role.MERLIN: 1,
            Role.LOYAL_SERVANT: 1,
            Role.ASSASSIN: 1,
            Role.MORGANA: 1,
            Role.MORDRED: 1  # This gives 3 evil roles, should be 2
        }
        with self.assertRaises(ValueError):
            AvalonGame(player_names, custom_roles)


class TestQuestConfiguration(unittest.TestCase):
    """Test quest configuration and setup."""
    
    def test_quest_team_sizes(self):
        """Test that quest team sizes are properly configured."""
        # For 5 players, quests should require [2, 3, 2, 3, 3] members
        game = AvalonGame(["P1", "P2", "P3", "P4", "P5"])
        expected_sizes = [2, 3, 2, 3, 3]
        for i, quest in enumerate(game.quests):
            self.assertEqual(quest.required_team_size, expected_sizes[i])
        
        # For 7 players, quests should require [2, 3, 3, 4, 4] members
        game = AvalonGame(["P1", "P2", "P3", "P4", "P5", "P6", "P7"])
        expected_sizes = [2, 3, 3, 4, 4]
        for i, quest in enumerate(game.quests):
            self.assertEqual(quest.required_team_size, expected_sizes[i])
    
    def test_quest_failures_required(self):
        """Test that quests require the correct number of failures to fail."""
        # For 5 players, all quests require 1 fail
        game = AvalonGame(["P1", "P2", "P3", "P4", "P5"])
        for quest in game.quests:
            self.assertEqual(quest.fails_required, 1)
        
        # For 7 players, the 4th quest (index 3) requires 2 fails
        game = AvalonGame(["P1", "P2", "P3", "P4", "P5", "P6", "P7"])
        self.assertEqual(game.quests[0].fails_required, 1)
        self.assertEqual(game.quests[1].fails_required, 1)
        self.assertEqual(game.quests[2].fails_required, 1)
        self.assertEqual(game.quests[3].fails_required, 2)  # 4th quest needs 2 fails
        self.assertEqual(game.quests[4].fails_required, 1)
        
        # For 10 players, both 4th and 5th quests require 2 fails
        game = AvalonGame(["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"])
        self.assertEqual(game.quests[0].fails_required, 1)
        self.assertEqual(game.quests[1].fails_required, 1)
        self.assertEqual(game.quests[2].fails_required, 1)
        self.assertEqual(game.quests[3].fails_required, 2)  # 4th quest needs 2 fails
        self.assertEqual(game.quests[4].fails_required, 2)  # 5th quest needs 2 fails


class TestGameFlow(unittest.TestCase):
    """Test the game flow mechanics."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a game with known roles for testing
        self.player_names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
        self.game = AvalonGame(self.player_names)
        
        # Set known roles for easier testing
        self.game.players[0].role = Role.MERLIN
        self.game.players[0].team = Team.GOOD
        self.game.players[1].role = Role.LOYAL_SERVANT
        self.game.players[1].team = Team.GOOD
        self.game.players[2].role = Role.LOYAL_SERVANT
        self.game.players[2].team = Team.GOOD
        self.game.players[3].role = Role.ASSASSIN
        self.game.players[3].team = Team.EVIL
        self.game.assassin = self.game.players[3]
        self.game.players[4].role = Role.MINION
        self.game.players[4].team = Team.EVIL
        
        # Set up the first quest
        self.game.phase = GamePhase.TEAM_BUILDING
        self.game.current_leader_idx = 0  # Alice is leader
    
    def test_team_proposal(self):
        """Test proposing a team."""
        leader = self.game.players[0]  # Alice
        team = [self.game.players[0], self.game.players[1]]  # Alice, Bob
        
        self.game.propose_team(leader, team)
        self.assertEqual(self.game.phase, GamePhase.TEAM_VOTING)
        self.assertEqual(self.game.get_current_quest().team, team)
    
    def test_team_proposal_invalid_leader(self):
        """Test that non-leaders cannot propose teams."""
        not_leader = self.game.players[1]  # Bob, not the leader
        team = [self.game.players[0], self.game.players[1]]  # Alice, Bob
        
        with self.assertRaises(ValueError):
            self.game.propose_team(not_leader, team)
    
    def test_team_voting(self):
        """Test voting for a team."""
        # Propose a team first
        leader = self.game.players[0]  # Alice
        team = [self.game.players[0], self.game.players[1]]  # Alice, Bob
        self.game.propose_team(leader, team)
        
        # Vote for the team
        self.game.vote_for_team(self.game.players[0], VoteType.APPROVE)
        self.game.vote_for_team(self.game.players[1], VoteType.APPROVE)
        self.game.vote_for_team(self.game.players[2], VoteType.APPROVE)
        self.game.vote_for_team(self.game.players[3], VoteType.REJECT)
        
        # At this point, voting is not complete
        self.assertEqual(self.game.phase, GamePhase.TEAM_VOTING)
        
        # Final vote completes the voting
        self.game.vote_for_team(self.game.players[4], VoteType.REJECT)
        
        # Team is approved (3 vs 2), proceed to quest
        self.assertEqual(self.game.phase, GamePhase.QUEST)
    
    def test_team_voting_rejection(self):
        """Test what happens when a team is rejected."""
        # Propose a team first
        leader = self.game.players[0]  # Alice
        team = [self.game.players[0], self.game.players[1]]  # Alice, Bob
        self.game.propose_team(leader, team)
        
        # Vote against the team (3 rejects, 2 approves)
        self.game.vote_for_team(self.game.players[0], VoteType.APPROVE)
        self.game.vote_for_team(self.game.players[1], VoteType.APPROVE)
        self.game.vote_for_team(self.game.players[2], VoteType.REJECT)
        self.game.vote_for_team(self.game.players[3], VoteType.REJECT)
        self.game.vote_for_team(self.game.players[4], VoteType.REJECT)
        
        # Team should be rejected, back to team building, next leader
        self.assertEqual(self.game.phase, GamePhase.TEAM_BUILDING)
        self.assertEqual(self.game.current_leader_idx, 1)  # Bob should be the new leader
        self.assertEqual(self.game.failed_votes_count, 1)
    
    def test_quest_success(self):
        """Test a quest that succeeds."""
        # Setup: propose and approve a team
        leader = self.game.players[0]  # Alice
        team = [self.game.players[0], self.game.players[1]]  # Alice, Bob (both good)
        self.game.propose_team(leader, team)
        
        for player in self.game.players:
            self.game.vote_for_team(player, VoteType.APPROVE)
        
        # All team members vote for success
        self.game.vote_on_quest(self.game.players[0], VoteType.SUCCESS)
        self.game.vote_on_quest(self.game.players[1], VoteType.SUCCESS)
        
        # Quest should succeed, move to next quest
        self.assertEqual(self.game.succeeded_quests, 1)
        self.assertEqual(self.game.failed_quests, 0)
        self.assertEqual(self.game.current_quest_idx, 1)
        self.assertEqual(self.game.phase, GamePhase.TEAM_BUILDING)
        self.assertEqual(self.game.current_leader_idx, 1)  # Bob should be the new leader
    
    def test_quest_failure(self):
        """Test a quest that fails."""
        # Setup: propose and approve a team with an evil member
        leader = self.game.players[0]  # Alice
        team = [self.game.players[0], self.game.players[4]]  # Alice (good), Eve (evil)
        self.game.propose_team(leader, team)
        
        for player in self.game.players:
            self.game.vote_for_team(player, VoteType.APPROVE)
        
        # Good player votes success, evil player votes fail
        self.game.vote_on_quest(self.game.players[0], VoteType.SUCCESS)
        self.game.vote_on_quest(self.game.players[4], VoteType.FAIL)
        
        # Quest should fail, move to next quest
        self.assertEqual(self.game.succeeded_quests, 0)
        self.assertEqual(self.game.failed_quests, 1)
        self.assertEqual(self.game.current_quest_idx, 1)
        self.assertEqual(self.game.phase, GamePhase.TEAM_BUILDING)
        self.assertEqual(self.game.current_leader_idx, 1)  # Bob should be the new leader
    
    def test_game_end_good_wins(self):
        """Test game ending with good team winning."""
        self.game.succeeded_quests = 2
        self.game.failed_quests = 2
        
        # Set up a successful quest to trigger victory
        leader = self.game.players[0]  # Alice
        team = [self.game.players[0], self.game.players[1]]  # Alice, Bob (both good)
        self.game.propose_team(leader, team)
        
        for player in self.game.players:
            self.game.vote_for_team(player, VoteType.APPROVE)
        
        # All team members vote for success
        self.game.vote_on_quest(self.game.players[0], VoteType.SUCCESS)
        self.game.vote_on_quest(self.game.players[1], VoteType.SUCCESS)
        
        # Good team won 3 quests, move to assassination phase
        self.assertEqual(self.game.succeeded_quests, 3)
        self.assertEqual(self.game.phase, GamePhase.ASSASSINATION)
    
    def test_game_end_evil_wins_by_quests(self):
        """Test game ending with evil team winning by failing quests."""
        self.game.succeeded_quests = 2
        self.game.failed_quests = 2
        
        # Set up a failed quest to trigger evil victory
        leader = self.game.players[0]  # Alice
        team = [self.game.players[0], self.game.players[4]]  # Alice (good), Eve (evil)
        self.game.propose_team(leader, team)
        
        for player in self.game.players:
            self.game.vote_for_team(player, VoteType.APPROVE)
        
        # Evil player votes to fail the quest
        self.game._set_dummy_phase(GamePhase.QUEST)
        self.game.vote_on_quest(self.game.players[0], VoteType.SUCCESS)
        self.game.vote_on_quest(self.game.players[4], VoteType.FAIL)
        
        #import pdb; pdb.set_trace()
        # Evil team won by failing 3 quests
        self.assertEqual(self.game.failed_quests, 3)
        self.assertEqual(self.game.phase, GamePhase.GAME_END)
        self.assertEqual(self.game.get_winner(), Team.EVIL)
    
    def test_assassination(self):
        """Test the assassination phase."""
        # Set up for assassination phase
        self.game.succeeded_quests = 3
        self.game.phase = GamePhase.ASSASSINATION
        
        # Assassin (Dave) tries to kill Merlin (Alice)
        self.game.assassinate(self.game.players[0])
        
        # Game should end, evil should win
        self.assertEqual(self.game.phase, GamePhase.GAME_END)
        self.assertEqual(self.game.get_winner(), Team.EVIL)
        
        # Reset game state
        self.setUp()
        self.game.succeeded_quests = 3
        self.game.phase = GamePhase.ASSASSINATION
        
        # Assassin misses Merlin, kills Bob instead
        self.game.assassinate(self.game.players[1])
        
        # Game should end, good should win
        self.assertEqual(self.game.phase, GamePhase.GAME_END)
        self.assertEqual(self.game.get_winner(), Team.GOOD)
    
    def test_visible_roles(self):
        """Test the role visibility rules."""
        # Merlin (Alice) can see evil players except Mordred
        merlin = self.game.players[0]
        visible_to_merlin = self.game.get_visible_roles(merlin)
        self.assertEqual(len(visible_to_merlin), 3)  # Merlin + 2 evil players
        self.assertIn(self.game.players[3], visible_to_merlin)  # Assassin
        self.assertIn(self.game.players[4], visible_to_merlin)  # Minion
        
        # Evil players can see each other
        evil_player = self.game.players[3]  # Assassin
        visible_to_evil = self.game.get_visible_roles(evil_player)
        self.assertEqual(len(visible_to_evil), 2)  # Self + other evil player
        self.assertIn(self.game.players[4], visible_to_evil)  # Minion


if __name__ == "__main__":
    unittest.main()