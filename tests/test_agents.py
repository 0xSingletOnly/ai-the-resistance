"""
Unit tests for Avalon agents.
"""
import unittest
from unittest.mock import MagicMock, patch
from game_engine.engine import Team, Role, VoteType, GamePhase
from game_engine.models import Player, Quest
from game_engine.game import AvalonGame
from game_engine.agents.base import RuleBasedAgent
from game_engine.agents.llm import LLMAgent

class TestRuleBasedAgent(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        # Create a test game with 5 players
        self.player_names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
        # Create players without roles
        self.players = [Player(name) for name in self.player_names]
        self.alice = self.players[0]
        self.bob = self.players[1]
        self.charlie = self.players[2]
        self.dave = self.players[3]
        self.eve = self.players[4]
        
        # Create a mock game object
        self.game = MagicMock(spec=AvalonGame)
        self.game.players = self.players
        self.game.phase = GamePhase.TEAM_BUILDING
        self.game.current_quest_idx = 0
        
        # Set up quest configuration
        mock_quest = MagicMock(spec=Quest)
        mock_quest.required_team_size = 2
        self.game.get_current_quest.return_value = mock_quest
        self.game.quests = [mock_quest] * 5
        
        # Set up default visible roles (empty by default)
        self.game.get_visible_roles.return_value = {}
    
    def test_propose_team_good_player(self):
        """Test that good players propose teams of the correct size."""
        # Set up a good player as the agent
        self.alice.assign_role(Role.MERLIN)
        agent = RuleBasedAgent(self.alice)
        
        # Test team proposal for each quest
        for quest in self.game.quests:
            self.game.current_quest_idx = self.game.quests.index(quest)
            proposed_team = agent.propose_team(self.game)
            
            # Verify team size
            self.assertEqual(len(proposed_team), quest.required_team_size, 
                           f"Quest {self.game.current_quest_idx + 1}: Wrong team size")
            
            # Verify agent is in the team
            self.assertIn(self.alice, proposed_team,
                         "Agent should include themselves in the team")
            
            # Verify all team members are valid players
            for player in proposed_team:
                self.assertIn(player, self.game.players,
                            "All team members should be valid players")
    
    def test_propose_team_evil_player(self):
        """Test that evil players try to include other evil players."""
        # Set up an evil player as the agent
        self.alice.assign_role(Role.ASSASSIN)
        self.bob.assign_role(Role.MINION)
        agent = RuleBasedAgent(self.alice)
        
        # Mock visible roles to show Bob as evil
        with patch('game_engine.game.AvalonGame.get_visible_roles') as mock_roles:
            mock_roles.return_value = {self.bob: Role.MINION}
            
            # Test team proposal
            proposed_team = agent.propose_team(self.game)
            
            # Verify team size
            self.assertEqual(len(proposed_team), self.game.get_current_quest().required_team_size,
                           "Wrong team size")
            
            # Verify agent is in the team
            self.assertIn(self.alice, proposed_team,
                         "Agent should include themselves in the team")
            
            # Verify the evil teammate is included if possible
            if len(proposed_team) > 1:
                evil_teammates = [p for p in proposed_team if p.team == Team.EVIL]
                self.assertGreaterEqual(len(evil_teammates), 1,
                                      "Evil player should try to include at least one evil teammate")
    
    def test_vote_for_team_good_player(self):
        """Test voting behavior of good players."""
        # Set up a good player as the agent
        self.alice.assign_role(Role.MERLIN)
        self.bob.assign_role(Role.LOYAL_SERVANT)
        self.charlie.assign_role(Role.MINION)
        agent = RuleBasedAgent(self.alice)
        
        # Test voting on different team compositions
        good_team = [self.alice, self.bob]  # Both good
        mixed_team = [self.alice, self.charlie]  # One good, one evil
        
        # When we can see both players are good
        self.game.get_visible_roles.return_value = {self.bob: Role.LOYAL_SERVANT}
        vote = agent.vote_for_team(self.game, good_team)
        self.assertEqual(vote, VoteType.APPROVE,
                       "Good player should approve teams with known good players")
        
        # When we can see an evil player
        self.game.get_visible_roles.return_value = {self.charlie: Role.MINION}
        vote = agent.vote_for_team(self.game, mixed_team)
        self.assertEqual(vote, VoteType.REJECT,
                       "Good player should reject teams with known evil players")
    
    def test_vote_for_team_evil_player(self):
        """Test voting behavior of evil players."""
        # Set up an evil player as the agent
        self.alice.assign_role(Role.ASSASSIN)
        self.bob.assign_role(Role.MINION)
        self.charlie.assign_role(Role.LOYAL_SERVANT)
        agent = RuleBasedAgent(self.alice)
        
        # Test voting on different team compositions
        evil_team = [self.alice, self.bob]  # Both evil
        mixed_team = [self.alice, self.charlie]  # One evil, one good
        
        # When we can see another evil player
        self.game.get_visible_roles.return_value = {self.bob: Role.MINION}
        vote = agent.vote_for_team(self.game, evil_team)
        self.assertEqual(vote, VoteType.APPROVE,
                       "Evil player should approve teams with known evil players")
        
        # When we don't see any evil players
        self.game.get_visible_roles.return_value = {}
        vote = agent.vote_for_team(self.game, mixed_team)
        self.assertEqual(vote, VoteType.REJECT,
                       "Evil player should reject teams without known evil players")
    
    def test_vote_on_quest_good_player(self):
        """Test that good players always vote SUCCESS on quests."""
        # Set up a good player as the agent
        self.alice.assign_role(Role.MERLIN)
        agent = RuleBasedAgent(self.alice)
        
        vote = agent.vote_on_quest(self.game)
        self.assertEqual(vote, VoteType.SUCCESS,
                        "Good players must always vote SUCCESS on quests")
    
    def test_vote_on_quest_evil_player(self):
        """Test that evil players can vote either SUCCESS or FAIL on quests."""
        # Set up an evil player as the agent
        self.alice.assign_role(Role.ASSASSIN)
        agent = RuleBasedAgent(self.alice)
        
        # Test multiple votes to ensure both SUCCESS and FAIL are possible
        votes = set()
        for _ in range(100):
            vote = agent.vote_on_quest(self.game)
            votes.add(vote)
            self.assertIn(vote, [VoteType.SUCCESS, VoteType.FAIL],
                         "Evil player vote must be either SUCCESS or FAIL")
        
        # Verify that evil players can vote both ways
        self.assertEqual(len(votes), 2,
                        "Evil players should be able to vote both SUCCESS and FAIL")

class TestLLMAgent(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        # Create a test game with 5 players
        self.player_names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
        # Create players without roles
        self.players = [Player(name) for name in self.player_names]
        self.alice = self.players[0]
        
        # Create a mock game object
        self.game = MagicMock(spec=AvalonGame)
        self.game.players = self.players
        self.game.phase = GamePhase.TEAM_BUILDING
        self.game.current_quest_idx = 0
        
        # Create quest history (all quests with no result yet)
        self.game.quests = []
        for i in range(5):
            quest = MagicMock(spec=Quest)
            quest.required_team_size = 2
            quest.result = None
            quest.team = None
            quest.pre_quest_votes = {}
            self.game.quests.append(quest)
        
        # Set up current quest
        self.game.get_current_quest.return_value = self.game.quests[0]
        
        # Set up default visible roles (empty by default)
        self.game.get_visible_roles.return_value = {}
        
        # Set up game state needed by LLM agent
        self.game.succeeded_quests = 0
        self.game.failed_quests = 0
        self.game.failed_votes_count = 0
        
        # Set up current leader
        self.game.get_current_leader.return_value = self.alice
    
    def test_llm_agent_fallback(self):
        """Test that LLM agent falls back to rule-based behavior when needed."""
        # Set up an LLM agent
        self.alice.assign_role(Role.MERLIN)
        agent = LLMAgent(self.alice)
        
        # Mock additional game state needed by LLM agent
        self.game.succeeded_quests = 0
        self.game.failed_quests = 0
        self.game.failed_votes_count = 0
        
        # Test team proposal (should fall back to rule-based)
        proposed_team = agent.propose_team(self.game)
        self.assertEqual(len(proposed_team), self.game.get_current_quest().required_team_size,
                        "Team size should be correct even in fallback mode")
        
        # Test team voting (should fall back to rule-based)
        vote = agent.vote_for_team(self.game, proposed_team)
        self.assertIn(vote, [VoteType.APPROVE, VoteType.REJECT],
                     "Vote should be valid even in fallback mode")
        
        # Test quest voting (should fall back to rule-based)
        vote = agent.vote_on_quest(self.game)
        self.assertEqual(vote, VoteType.SUCCESS,
                        "Good players must vote SUCCESS even in fallback mode")

if __name__ == '__main__':
    unittest.main()
