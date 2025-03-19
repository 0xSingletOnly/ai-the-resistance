"""
LLM-based agent implementation for The Resistance: Avalon.
"""
from dotenv import load_dotenv
from openai import AsyncOpenAI
from typing import List, Dict, Optional
import json
import os
import asyncio
import re

from ..enums import Team, Role, VoteType, GamePhase
from ..models import Player, Quest
from ..game import AvalonGame
from .base import AvalonAgent, RuleBasedAgent
import logging
import datetime
import pathlib

load_dotenv()

# Set up logging
log_dir = pathlib.Path("logs/llm_responses")
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"llm_responses_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

class LLMAgent(AvalonAgent):
    """
    LLM-based agent that uses language models for decision making.
    """
    
    def __init__(self, player: Player, model_name: str = "deepseek-chat", use_cot: bool = False):
        super().__init__(player)
        self.model_name = model_name
        self.use_cot = use_cot
        self.conversation_history = []
        
    def _log_llm_response(self, turn_type: str, prompt: str, response: str):
        """Log LLM response with metadata for training purposes."""
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "player_role": self.player.role.value if self.player.role else None,
            "turn_type": turn_type,
            "prompt": prompt,
            "response": response,
            "model": self.model_name,
            "use_cot": self.use_cot,
        }
        
        # Log to file for training data
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
            
        # Log to standard logger for system monitoring
        logger.info(f"LLM response for player {self.player.name}, role {self.player.role.value}, turn type {turn_type}, response: {response}")
    
    def _get_game_state_prompt(self, game: AvalonGame) -> str:
        """Create a detailed prompt describing the current game state."""
        visible_roles = game.get_visible_roles(self.player)
        
        state = {
            "player_info": {
                "name": self.player.name,
                "role": self.player.role.value,
                "team": self.player.team.value,
                "visible_roles": {
                    p.name: role.value for p, role in visible_roles.items()
                }
            },
            "game_state": {
                "players": [p.name for p in game.players],
                "phase": game.phase.value,
                "current_quest": game.current_quest_idx + 1,
                "succeeded_quests": game.succeeded_quests,
                "failed_quests": game.failed_quests,
                "current_leader": game.get_current_leader().name,
                "failed_votes_count": game.failed_votes_count
            },
            "quest_history": []
        }
        
        # Add quest history
        for i, quest in enumerate(game.quests):
            if quest.result:
                quest_info = {
                    "quest_number": i + 1,
                    "result": quest.result.value,
                    "team": [p.name for p in quest.team] if quest.team else [],
                    "votes": {p.name: v.value for p, v in quest.pre_quest_votes.items()}
                }
                state["quest_history"].append(quest_info)
        
        base_prompt = f"""You are playing The Resistance: Avalon as player {self.player.name}.
Current game state:
{json.dumps(state, indent=2)}

Make decisions based on this information and your role's objectives:
- Good team (Merlin, Percival, Loyal Servants) must succeed 3 quests
- Evil team (Assassin, Morgana, Minions) must either:
  1. Fail 3 quests, or
  2. Successfully assassinate Merlin at the end or
  3. Five team proposals are rejected consecutively

Remember:
1. Only evil players can vote FAIL on quests
2. Team proposals need majority approval
3. Most quests fail with 1 FAIL vote (some need 2)
4. Maintain your role's secrecy while achieving your team's objectives
"""

        if self.use_cot:
            base_prompt += """
Before responding, think through these steps internally (but do not include your thought process in the response):
1. First, analyze the current game state and quest history
2. Consider your role and team's objectives
3. Evaluate the information visible to you about other players
4. Think about how your decision impacts your team's strategy
5. Make your decision based on this analysis

IMPORTANT: Only provide the final answer in your response, not your reasoning.
"""

        return base_prompt

    async def _get_llm_response_async(self, prompt: str) -> str:
        """Get a response from the language model asynchronously."""
        try:
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM API call failed: {e}")
            return "FALLBACK"

    def propose_team(self, game: AvalonGame) -> List[Player]:
        """Use LLM to propose a quest team based on game state and strategy."""
        prompt = self._get_game_state_prompt(game)
        if self.use_cot:
            prompt += f"\nCarefully analyze which {game.get_current_quest().required_team_size} players to propose for the current quest. Consider the game state and team dynamics in your mind, but respond with only a JSON list of player names."
        else:
            prompt += f"\nYou need to propose a team of {game.get_current_quest().required_team_size} players for the current quest.\nRespond with only your chosen team as a JSON list of player names."
        
        # Run async API call in sync context
        response = asyncio.run(self._get_llm_response_async(prompt))
        print(f"Response from propose_team is: {response}")
        if response == "FALLBACK":
            # Fallback to rule-based behavior
            print(f"{self.player.name}, who is {self.player.role}, failed to use LLM to propose team, defaulting to rule-based behavior")
            return RuleBasedAgent(self.player).propose_team(game)
        
        try:
            team_names = json.loads(re.search(r'```json\n(.*)\n```', response, re.DOTALL).group(1))
            self._log_llm_response("PROPOSE_TEAM", prompt, response)
            return [p for p in game.players if p.name in team_names]
        except:
            print(f"{self.player.name}, who is {self.player.role}, failed to use LLM to propose team, falling back to rule-based behavior")
            # Fallback to rule-based behavior on error
            return RuleBasedAgent(self.player).propose_team(game)

    async def vote_for_team_async(self, game: AvalonGame, proposed_team: List[Player]) -> VoteType:
        """Async version of vote_for_team."""
        prompt = self._get_game_state_prompt(game)
        prompt += f"\nProposed team: {[p.name for p in proposed_team]}"
        if self.use_cot:
            prompt += "\nCarefully analyze whether to approve or reject this team. Consider the team composition and game state in your mind, but respond with only APPROVE or REJECT."
        else:
            prompt += "\nShould you approve (APPROVE) or reject (REJECT) this team? Respond with exactly one of these options."
        
        response = await self._get_llm_response_async(prompt)
        if response == "FALLBACK":
            print(f"{self.player.name}, who is {self.player.role}, failed to use LLM to vote for team, defaulting to rule-based behavior")
            return RuleBasedAgent(self.player).vote_for_team(game, proposed_team)
        
        try:
            vote = response.strip().split()[0].upper()
            if vote not in ["APPROVE", "REJECT"]:
                raise ValueError(f"Invalid vote: {vote}")
                
            self._log_llm_response("VOTE_FOR_TEAM", prompt, response)
            return VoteType.APPROVE if vote == "APPROVE" else VoteType.REJECT
            
        except Exception as e:
            print(f"{self.player.name}, who is {self.player.role}, failed to parse LLM vote response: {str(e)}, defaulting to rule-based behavior")
            return RuleBasedAgent(self.player).vote_for_team(game, proposed_team)

    def vote_for_team(self, game: AvalonGame, proposed_team: List[Player]) -> VoteType:
        """Synchronous wrapper for vote_for_team_async."""
        return asyncio.run(self.vote_for_team_async(game, proposed_team))

    async def vote_on_quest_async(self, game: AvalonGame) -> VoteType:
        """Async version of vote_on_quest."""
        if self.player.team == Team.GOOD:
            return VoteType.SUCCESS  # Good players must succeed
        
        prompt = self._get_game_state_prompt(game)
        if self.use_cot:
            prompt += "\nAs an evil player, carefully analyze whether you should succeed or fail this quest. Consider the game state and potential consequences in your mind, but respond with only SUCCESS or FAIL."
        else:
            prompt += "\nAs an evil player, should you succeed (SUCCESS) or fail (FAIL) this quest? Respond with exactly one of these options."
        
        response = await self._get_llm_response_async(prompt)
        if response == "FALLBACK":
            print(f"{self.player.name}, who is {self.player.role}, failed to use LLM to vote on quest, defaulting to rule-based behavior")
            return RuleBasedAgent(self.player).vote_on_quest(game)
        
        self._log_llm_response("VOTE_ON_QUEST", prompt, response)
        return VoteType.FAIL if response.strip().upper() == "FAIL" else VoteType.SUCCESS

    def vote_on_quest(self, game: AvalonGame) -> VoteType:
        """Synchronous wrapper for vote_on_quest_async."""
        return asyncio.run(self.vote_on_quest_async(game))

    async def choose_assassination_target_async(self, game: AvalonGame) -> Player:
        """Async version of choose_assassination_target."""
        if self.player.role != Role.ASSASSIN:
            raise ValueError("Only the Assassin can choose assassination targets")
        
        prompt = self._get_game_state_prompt(game)
        prompt += "\nAs the Assassin, which player do you think is Merlin? Respond with exactly one player name."
        
        response = await self._get_llm_response_async(prompt)
        if response == "FALLBACK":
            return RuleBasedAgent(self.player).choose_assassination_target(game)
        
        target_name = response.strip()
        targets = [p for p in game.players if p.name == target_name]
        if targets:
            self._log_llm_response("ASSASSINATION_TARGET", prompt, response)
            return targets[0]
        else:
            print(f"LLM failed to choose assassination target, defaulting to rule-based behavior")
            return RuleBasedAgent(self.player).choose_assassination_target(game)

    def choose_assassination_target(self, game: AvalonGame) -> Player:
        """Synchronous wrapper for choose_assassination_target_async."""
        return asyncio.run(self.choose_assassination_target_async(game))
