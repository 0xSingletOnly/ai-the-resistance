"""
A simple example that demonstrates the use of the Avalon game engine with both rule-based and LLM agents.
"""
import builtins
import sys
import os
import random
import time

import multiprocessing
from typing import List, Dict, Type, Optional
from collections import defaultdict

# Add the parent directory to the path so we can import the game engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_engine.engine import Team, Role, GamePhase, VoteType, AvalonGame
from game_engine.utils import generate_game_id, setup_game_logger, log_game_event, save_game_state
from game_engine.metrics.evaluator import GameEvaluator
from game_engine.agents.base import AvalonAgent, RuleBasedAgent
from game_engine.agents.llm import LLMAgent

from game_engine.config import MAX_FAILED_VOTES
from game_engine.enums import QuestResult


def print_player_info(game: AvalonGame, player_idx: int):
    """Print information visible to a specific player"""
    player = game.players[player_idx]
    print(f"\n=== Information for {player.name} ===")
    print(f"Role: {player.role.value}")
    print(f"Team: {player.team.value}")
    
    # Show visible roles
    visible_roles = game.get_visible_roles(player)
    if len(visible_roles) > 1:  # More than just the player's own role
        print("\nPlayers you can identify:")
        for p, role in visible_roles.items():
            if p != player:
                print(f"  {p.name} as {role.value}")
    
    print("\n")


def print_game_state(game: AvalonGame):
    """Print the public game state"""
    print("\n=== Game State ===")
    print(f"Phase: {game.phase.value}")
    print(f"Current Quest: {game.current_quest_idx + 1}")
    print(f"Succeeded Quests: {game.succeeded_quests}")
    print(f"Failed Quests: {game.failed_quests}")
    print(f"Current Leader: {game.get_current_leader().name}")
    
    # Display voting history for all players
    print("\nVoting History:")
    for player in game.players:
        print(f"\n{player.name}:")
        if player.team_vote_history:
            print("  Team votes:")
            for record in player.team_vote_history:
                quest_result = f" ({record.quest_result.value})" if record.quest_result else ""
                print(f"    Quest {record.quest_number}{quest_result} - Leader {record.leader}")
                print(f"      Team: {', '.join(record.proposed_team)}")
                print(f"      Vote: {record.vote.value}")
        else:
            print("  No team votes yet")
            
        # Only show quest votes if the game is over
        if game.phase == GamePhase.GAME_END and player.quest_vote_history:
            print("  Quest votes:")
            for record in player.quest_vote_history:
                print(f"    Quest {record.quest_number}")
                print(f"      Team: {', '.join(record.team)}")
                print(f"      Vote: {record.vote.value}")
    
    # Display quests information
    print("\nQuests:")
    for i, quest in enumerate(game.quests):
        status = "Current" if i == game.current_quest_idx else "Complete" if quest.result != None else "Upcoming"
        result = quest.result.value if quest.result else "N/A"
        print(f"  Quest {i+1}: {status}, Result: {result}, Team Size: {quest.required_team_size}")
    
    # If in team building or voting phase, show the proposed team
    current_quest = game.get_current_quest()
    if game.phase in [GamePhase.TEAM_BUILDING, GamePhase.TEAM_VOTING] and current_quest.team:
        print("\nProposed Team:")
        for player in current_quest.team:
            print(f"  {player.name}")
    
    print("\n")


def gather_team_votes(agents, game, proposed_team):
    """Gather team votes sequentially."""
    votes = {}
    for player, agent in agents.items():
        votes[player] = agent.vote_for_team(game, proposed_team)
    return votes

def gather_quest_votes(agents, game, team):
    """Gather quest votes sequentially."""
    votes = {}
    for player, agent in agents.items():
        votes[player] = agent.vote_on_quest(game)
    return votes

def run_simple_game(agent_type: Type[AvalonAgent] = RuleBasedAgent, model_name: Optional[str] = None, use_cot: bool = False):
    """
    Run a simple example game with the specified agent type.
    
    Args:
        agent_type: Type of agent to use (RuleBasedAgent or LLMAgent)
        model_name: Name of the LLM model to use (only for LLMAgent)
        
    Returns:
        AvalonGame: The completed game object
    """
    # Create a game with 5 players
    player_names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
    game = AvalonGame(player_names)
    
    # Create agents for each player
    agents = {}
    for player in game.players:
        if agent_type == LLMAgent and model_name:
            agents[player] = LLMAgent(player, model_name, use_cot)
        else:
            agents[player] = agent_type(player)
    
    # Generate a game ID and setup logging
    game_id = generate_game_id()
    logger = setup_game_logger(game_id)
    
    print(f"Starting a new game with ID: {game_id}")
    print(f"Players: {', '.join(player_names)}")
    print(f"Agent type: {agent_type.__name__}")
    
    # Log game setup
    log_game_event(logger, "game_setup", {
        "players": player_names,
        "player_count": game.player_count,
        "agent_type": agent_type.__name__
    })
    
    # Show each player their role
    for i in range(game.player_count):
        print_player_info(game, i)
    
    # Start the game - move from SETUP to TEAM_BUILDING
    game.phase = GamePhase.TEAM_BUILDING
    
    # Main game loop
    while not game.is_game_over():
        print_game_state(game)
        
        if game.phase == GamePhase.TEAM_BUILDING:
            # Current leader proposes a team
            leader = game.get_current_leader()
            quest = game.get_current_quest()
            
            # Use agent to propose team
            team = agents[leader].propose_team(game)
            
            print(f"{leader.name} proposes a team: {', '.join(player.name for player in team)}")
            game.propose_team(leader, team)
            
            # Log team proposal
            log_game_event(logger, "team_proposed", {
                "leader": leader.name,
                "team": [player.name for player in team],
                "quest_number": game.current_quest_idx + 1
            })
            
        elif game.phase == GamePhase.TEAM_VOTING:
            # All players vote on the proposed team concurrently
            print("\nVoting on the proposed team:")
            proposed_team = game.get_current_quest().team
            
            # Gather all votes sequentially
            votes = gather_team_votes(agents, game, proposed_team)
            
            # Process all votes
            for player, vote in votes.items():
                print(f"  {player.name} votes: {vote.value}")
                game.vote_for_team(player, vote)
            
        elif game.phase == GamePhase.QUEST:
            # Team members go on the quest
            quest = game.get_current_quest()
            team = quest.team
            
            print(f"\nTeam {', '.join(player.name for player in team)} goes on Quest {game.current_quest_idx + 1}")
            
            # Gather all quest votes from players participating in quest sequentially
            agents_in_quest = {player: agents[player] for player in team}
            quest_votes = gather_quest_votes(agents_in_quest, game, team)
            
            # Process all votes
            for player, vote in quest_votes.items():
                game.vote_on_quest(player, vote)
            
            # Determine the result
            result = quest.process_result()
            
            # current_quest_idx incremented in `process_result`
            print(f"Quest {game.current_quest_idx} {result.value}!")
            
            # To maintain secrecy, only show the count of fail votes, not who voted fail
            fail_count = sum(1 for v in quest_votes.values() if v == VoteType.FAIL)
            print(f"There were {fail_count} fail votes.")
            
            # Log quest result
            log_game_event(logger, "quest_result", {
                "quest_number": game.current_quest_idx,
                "result": result.value,
                "fail_votes": fail_count
            })
            
        elif game.phase == GamePhase.ASSASSINATION:
            # Assassin tries to identify Merlin
            assassin = game.assassin
            
            # Find Merlin
            merlin = next((p for p in game.players if p.role == Role.MERLIN), None)
            
            # Simple strategy: assassin randomly guesses (could be more sophisticated)
            # Only target good players since assassin knows who evil players are
            good_players = [p for p in game.players if p.team == Team.GOOD]
            target = random.choice(good_players)
            
            print(f"\n{assassin.name} (Assassin) attempts to assassinate {target.name}")
            game.assassinate(target)
            
            # Log assassination
            log_game_event(logger, "assassination", {
                "assassin": assassin.name,
                "target": target.name,
                "target_was_merlin": target == merlin
            })
    
    # Game is over
    print_game_state(game)
    
    # Determine the winner and explain why they won
    winner = game.get_winner()
    print("\nGame over!")
    
    if winner == Team.GOOD:
        print("Good team wins by successfully completing 3 quests!")
    else:  # Evil team won
        if game.failed_votes_count >= MAX_FAILED_VOTES:
            print("Evil team wins by causing distrust - 5 consecutive team proposals were rejected!")
        elif game.failed_quests >= 3:
            print("Evil team wins by failing 3 quests!")
        elif game.assassinated_player and game.assassinated_player.role == Role.MERLIN:
            print("Evil team wins by successfully assassinating Merlin!")
    
    # Show all player roles
    print("\nPlayer roles were:")
    for player in game.players:
        print(f"  {player.name}: {player.role.value} ({player.team.value})")
    
    # Calculate and log game metrics
    metrics = GameEvaluator.evaluate_game(game)
    print("\nGame Metrics:")
    print("Team Metrics:", metrics["team_metrics"])
    print("Deception Metrics:", metrics["deception_metrics"])
    
    # Log game end
    log_game_event(logger, "game_end", {
        "winner": winner.value,
        "succeeded_quests": game.succeeded_quests,
        "failed_quests": game.failed_quests,
        "metrics": metrics
    })
    
    # Save final game state
    save_game_state(game.get_game_state(), game_id)
    
    return game


def run_single_batch(batch_size: int, batch_num: int, agent_type: Type[AvalonAgent] = RuleBasedAgent, model_name: Optional[str] = None, use_cot: bool = False) -> Dict:
    print(f"Starting batch {batch_num} ({batch_size} games)...")
    """Run a batch of games and collect statistics
    
    Args:
        batch_size: Number of games to run in this batch
        agent_type: Type of agent to use (RuleBasedAgent or LLMAgent)
        model_name: Name of the LLM model to use (only for LLMAgent)
        
    Returns:
        Dict containing statistics for this batch of games
    """
    stats = {
        "wins": defaultdict(int),
        "evil_wins_by": {
            "failed_quests": 0,
            "assassinated_merlin": 0,
            "failed_team_proposals": 0
        },
        "total_games": batch_size,
        "evil_deception_success": {
            "total_evil_on_quests": 0,
            "total_evil_proposed": 0,
            "total_evil_opportunities": 0
        }
    }
    
    try:
        for game_num in range(batch_size):
            print(f"Starting game {game_num + 1} in batch {batch_num}...")
            # Temporarily disable printing for game execution
            # def silent_print(*args, **kwargs):
            #     pass
            # builtins.print = silent_print
            
            # Run the game
            game = run_simple_game(agent_type, model_name, use_cot)
            
            winner = game.get_winner()
            stats["wins"][winner.value] += 1
            
            # Track how evil team won
            if winner == Team.EVIL:
                if game.failed_votes_count >= MAX_FAILED_VOTES:
                    stats["evil_wins_by"]["failed_team_proposals"] += 1
                elif game.failed_quests >= 3:
                    stats["evil_wins_by"]["failed_quests"] += 1
                elif game.assassinated_player and game.assassinated_player.role == Role.MERLIN:
                    stats["evil_wins_by"]["assassinated_merlin"] += 1
            
            # Only count quests that were actually completed
            completed_quests = game.succeeded_quests + game.failed_quests
            for i in range(completed_quests):
                quest = game.quests[i]
                if quest.result != QuestResult.NOT_STARTED:  # Only count completed quests
                    if quest.team:
                        evil_players_proposed = sum(1 for p in quest.team if p.team == Team.EVIL)
                        stats["evil_deception_success"]["total_evil_proposed"] += evil_players_proposed
                        stats["evil_deception_success"]["total_evil_opportunities"] += len(quest.team)
                        
                        # Count successful sabotage (fail votes by evil players)
                        if quest.in_quest_votes:
                            for player, vote in quest.in_quest_votes.items():
                                if player.team == Team.EVIL and vote == VoteType.FAIL:
                                    stats["evil_deception_success"]["total_evil_on_quests"] += 1
    finally:
        print(f"Completed batch {batch_num} ({batch_size} games)")
    
    return stats

def merge_stats(stats_list: List[Dict]) -> Dict:
    """Merge multiple stats dictionaries into one
    
    Args:
        stats_list: List of stats dictionaries to merge
        
    Returns:
        Dict containing merged statistics
    """
    merged = {
        "wins": defaultdict(int),
        "evil_wins_by": {
            "failed_quests": 0,
            "assassinated_merlin": 0,
            "failed_team_proposals": 0
        },
        "total_games": 0,
        "evil_deception_success": {
            "total_evil_on_quests": 0,
            "total_evil_proposed": 0,
            "total_evil_opportunities": 0
        }
    }
    
    for stats in stats_list:
        # Merge wins
        for team, wins in stats["wins"].items():
            merged["wins"][team] += wins
        
        # Merge evil wins breakdown
        for key in merged["evil_wins_by"]:
            merged["evil_wins_by"][key] += stats["evil_wins_by"][key]
        
        # Merge total games
        merged["total_games"] += stats["total_games"]
        
        # Merge evil deception metrics
        for key in merged["evil_deception_success"]:
            merged["evil_deception_success"][key] += stats["evil_deception_success"][key]
    
    return merged

def run_multiple_games(num_games: int = 100, agent_type: Type[AvalonAgent] = RuleBasedAgent, model_name: Optional[str] = None, use_cot: bool = False):
    """Run multiple games sequentially and collect statistics
    
    Args:
        num_games: Total number of games to run
        agent_type: Type of agent to use (RuleBasedAgent or LLMAgent)
        model_name: Name of the LLM model to use (only for LLMAgent)
        use_cot: Whether to use chain of thought reasoning (only for LLMAgent)
    """
    start_time = time.time()
    print(f"Running {num_games} games with {agent_type.__name__}...")
    
    # Initialize statistics
    stats = {
        "wins": defaultdict(int),
        "evil_wins_by": {
            "failed_quests": 0,
            "assassinated_merlin": 0,
            "failed_team_proposals": 0
        },
        "total_games": 0,
        "evil_deception_success": {
            "total_evil_on_quests": 0,
            "total_evil_proposed": 0,
            "total_evil_opportunities": 0
        }
    }
    
    # Run games sequentially
    for game_num in range(num_games):
        print(f"\nStarting game {game_num + 1}/{num_games}...")
        
        # Run the game
        game = run_simple_game(agent_type, model_name, use_cot)
        
        # Update statistics
        winner = game.get_winner()
        stats["wins"][winner.value] += 1
        stats["total_games"] += 1
        
        # Track how evil team won
        if winner == Team.EVIL:
            if game.failed_votes_count >= MAX_FAILED_VOTES:
                stats["evil_wins_by"]["failed_team_proposals"] += 1
            elif game.failed_quests >= 3:
                stats["evil_wins_by"]["failed_quests"] += 1
            elif game.assassinated_player and game.assassinated_player.role == Role.MERLIN:
                stats["evil_wins_by"]["assassinated_merlin"] += 1
        
        # Only count quests that were actually completed
        completed_quests = game.succeeded_quests + game.failed_quests
        for i in range(completed_quests):
            quest = game.quests[i]
            if quest.result != QuestResult.NOT_STARTED:  # Only count completed quests
                if quest.team:
                    evil_players_proposed = sum(1 for p in quest.team if p.team == Team.EVIL)
                    stats["evil_deception_success"]["total_evil_proposed"] += evil_players_proposed
                    stats["evil_deception_success"]["total_evil_opportunities"] += len(quest.team)
                    
                    # Count successful sabotage (fail votes by evil players)
                    if quest.in_quest_votes:
                        for player, vote in quest.in_quest_votes.items():
                            if player.team == Team.EVIL and vote == VoteType.FAIL:
                                stats["evil_deception_success"]["total_evil_on_quests"] += 1
        
    
    # Print final statistics
    print("\nFinal Statistics:")
    print("=" * 50)
    print("Win Rates:")
    for team, wins in stats["wins"].items():
        win_rate = (wins / stats["total_games"]) * 100
        print(f"{team}: {win_rate:.1f}% ({wins}/{stats['total_games']})")
    
    # Print evil team win breakdown
    evil_wins = stats["wins"].get("Evil", 0)
    if evil_wins > 0:
        print("\nEvil Team Win Breakdown:")
        for win_type, count in stats["evil_wins_by"].items():
            percentage = (count / evil_wins) * 100
            print(f"- {win_type.replace('_', ' ').title()}: {percentage:.1f}% ({count}/{evil_wins})")
    
    print("\nEvil Team Deception Metrics:")
    if stats["evil_deception_success"]["total_evil_opportunities"] > 0:
        evil_proposed_rate = (stats["evil_deception_success"]["total_evil_proposed"] / 
                            stats["evil_deception_success"]["total_evil_opportunities"]) * 100
        print(f"Evil players proposed for quests: {evil_proposed_rate:.1f}%")
        
        if stats["evil_deception_success"]["total_evil_proposed"] > 0:
            evil_success_rate = (stats["evil_deception_success"]["total_evil_on_quests"] / 
                               stats["evil_deception_success"]["total_evil_proposed"]) * 100
            print(f"Evil players successfully sabotaged when on quest: {evil_success_rate:.1f}%")
    else:
        print("No quests were completed (all games ended due to failed team proposals)")
    
    end_time = time.time()
    total_time = (end_time - start_time) / 60
    print(f"\nTotal time taken: {total_time:.2f} minutes")

if __name__ == "__main__":
    # Run a single game with rule-based agents
    # print("Running a game with rule-based agents...")
    # run_simple_game(RuleBasedAgent)
    
    # Run a single game with LLM agents
    # print("\nRunning a game with LLM agents...")
    #run_simple_game(LLMAgent, model_name="qwen2.5-7b-instruct")
    run_multiple_games(num_games=50, agent_type=LLMAgent, model_name="ft:open-mistral-7b:5389c2d2:20250321:398b5c3a", use_cot=True) 

    # Run multiple games in batches with LLM agents
    # run_multiple_games(num_games=50, agent_type=LLMAgent, model_name="deepseek-chat", use_cot=True, batch_size=10)