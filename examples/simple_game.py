"""
A simple example that demonstrates the use of the Avalon game engine with both rule-based and LLM agents.
"""
import sys
import os
import random
from typing import List, Dict, Type, Optional
from collections import defaultdict

# Add the parent directory to the path so we can import the game engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_engine.engine import Team, Role, GamePhase, VoteType, AvalonGame
from game_engine.utils import generate_game_id, setup_game_logger, log_game_event, save_game_state
from game_engine.metrics.evaluator import GameEvaluator
from game_engine.agents.base import AvalonAgent, RuleBasedAgent
from game_engine.agents.llm import LLMAgent


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


def run_simple_game(agent_type: Type[AvalonAgent] = RuleBasedAgent, model_name: Optional[str] = None):
    """
    Run a simple example game with the specified agent type.
    
    Args:
        agent_type: Type of agent to use (RuleBasedAgent or LLMAgent)
        model_name: Name of the LLM model to use (only for LLMAgent)
    """
    # Create a game with 5 players
    player_names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
    game = AvalonGame(player_names)
    
    # Create agents for each player
    agents = {}
    for player in game.players:
        if agent_type == LLMAgent and model_name:
            agents[player] = LLMAgent(player, model_name)
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
            # All players vote on the proposed team
            print("\nVoting on the proposed team:")
            votes = {}
            proposed_team = game.get_current_quest().team
            
            for player in game.players:
                # Use agent to decide vote
                vote = agents[player].vote_for_team(game, proposed_team)
                votes[player] = vote
                
                print(f"  {player.name} votes: {vote.value}")
                game.vote_for_team(player, vote)
            
            # Log team votes
            log_game_event(logger, "team_votes", {
                "votes": {player.name: vote.value for player, vote in votes.items()},
                "quest_number": game.current_quest_idx + 1
            })
            
        elif game.phase == GamePhase.QUEST:
            # Team members go on the quest
            quest = game.get_current_quest()
            team = quest.team
            
            print(f"\nTeam {', '.join(player.name for player in team)} goes on Quest {game.current_quest_idx + 1}")
            
            # Each team member votes on the quest
            quest_votes = {}
            
            for player in team:
                # Use agent to decide quest vote
                vote = agents[player].vote_on_quest(game)
                quest_votes[player] = vote
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
    
    # Determine the winner
    winner = game.get_winner()
    print(f"\nGame over! {winner.value} team wins!")
    
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


def run_multiple_games(num_games: int = 100):
    """Run multiple games and collect statistics"""
    stats = {
        "wins": defaultdict(int),
        "total_games": num_games,
        "evil_deception_success": {
            "total_evil_on_quests": 0,
            "total_evil_proposed": 0,
            "total_evil_opportunities": 0  # number of quest slots available
        }
    }
    
    print(f"Running {num_games} games...")
    
    for game_num in range(num_games):
        # Create a game with 5 players
        player_names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
        game = AvalonGame(player_names)
        
        # Generate a game ID and setup logging
        game_id = generate_game_id()
        logger = setup_game_logger(game_id)
        
        # Start the game - move from SETUP to TEAM_BUILDING
        game.phase = GamePhase.TEAM_BUILDING
        
        # Main game loop
        while not game.is_game_over():
            if game.phase == GamePhase.TEAM_BUILDING:
                leader = game.get_current_leader()
                quest = game.get_current_quest()
                team_size = quest.required_team_size
                team = random.sample(game.players, team_size)
                game.propose_team(leader, team)
                
            elif game.phase == GamePhase.TEAM_VOTING:
                votes = {}
                for player in game.players:
                    team = game.get_current_quest().team
                    good_count = sum(1 for p in team if p.team == Team.GOOD)
                    evil_count = len(team) - good_count
                    
                    if player.team == Team.GOOD:
                        approve_probability = 0.5 + (good_count / len(team)) * 0.3
                    else:
                        approve_probability = 0.4 + (evil_count / len(team)) * 0.4
                    
                    vote = VoteType.APPROVE if random.random() < approve_probability else VoteType.REJECT
                    votes[player] = vote
                    game.vote_for_team(player, vote)
                
            elif game.phase == GamePhase.QUEST:
                quest = game.get_current_quest()
                team = quest.team
                quest_votes = {}
                
                # Count evil players proposed for this quest
                evil_players_proposed = sum(1 for p in team if p.team == Team.EVIL)
                stats["evil_deception_success"]["total_evil_proposed"] += evil_players_proposed
                stats["evil_deception_success"]["total_evil_opportunities"] += len(team)
                
                for player in team:
                    if player.team == Team.GOOD:
                        vote = VoteType.SUCCESS
                    else:
                        vote_fail_probability = 0.7
                        vote = VoteType.FAIL if random.random() < vote_fail_probability else VoteType.SUCCESS
                        if vote == VoteType.FAIL:
                            stats["evil_deception_success"]["total_evil_on_quests"] += 1
                    
                    quest_votes[player] = vote
                    game.vote_on_quest(player, vote)
                
                quest.process_result()
                
            elif game.phase == GamePhase.ASSASSINATION:
                assassin = game.assassin
                good_players = [p for p in game.players if p.team == Team.GOOD]
                target = random.choice(good_players)
                game.assassinate(target)
        
        # Game is over, collect stats
        winner = game.get_winner()
        stats["wins"][winner.value] += 1
        
        # Calculate metrics for this game
        metrics = GameEvaluator.evaluate_game(game)
        
        if (game_num + 1) % 10 == 0:
            print(f"Completed {game_num + 1} games...")
    
    # Print final statistics
    print("\nFinal Statistics:")
    print("=" * 50)
    print("Win Rates:")
    for team, wins in stats["wins"].items():
        win_rate = (wins / stats["total_games"]) * 100
        print(f"{team}: {win_rate:.1f}% ({wins}/{stats['total_games']})")
    
    print("\nEvil Team Deception Metrics:")
    evil_proposed_rate = (stats["evil_deception_success"]["total_evil_proposed"] / 
                         stats["evil_deception_success"]["total_evil_opportunities"]) * 100
    print(f"Evil players proposed for quests: {evil_proposed_rate:.1f}%")
    
    if stats["evil_deception_success"]["total_evil_proposed"] > 0:
        evil_success_rate = (stats["evil_deception_success"]["total_evil_on_quests"] / 
                           stats["evil_deception_success"]["total_evil_proposed"]) * 100
        print(f"Evil players successfully sabotaged when on quest: {evil_success_rate:.1f}%")

if __name__ == "__main__":
    # Run a single game with rule-based agents
    print("Running a game with rule-based agents...")
    run_simple_game(RuleBasedAgent)
    
    # Run a single game with LLM agents (commented out until LLM integration is complete)
    # print("\nRunning a game with LLM agents...")
    # run_simple_game(LLMAgent, model_name="gpt-3.5-turbo")