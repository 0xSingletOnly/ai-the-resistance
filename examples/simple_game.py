"""
A simple example that demonstrates the use of the Avalon game engine.
"""
import sys
import os
import random
from typing import List, Dict

# Add the parent directory to the path so we can import the game engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_engine.engine import AvalonGame, Team, Role, GamePhase, VoteType
from game_engine.utils import generate_game_id, setup_game_logger, log_game_event, save_game_state


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


def run_simple_game():
    """Run a simple example game with automatic/random choices"""
    # Create a game with 5 players
    player_names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
    game = AvalonGame(player_names)
    
    # Generate a game ID and setup logging
    game_id = generate_game_id()
    logger = setup_game_logger(game_id)
    
    print(f"Starting a new game with ID: {game_id}")
    print(f"Players: {', '.join(player_names)}")
    
    # Log game setup
    log_game_event(logger, "game_setup", {
        "players": player_names,
        "player_count": game.player_count
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
            team_size = quest.required_team_size
            
            # Randomly select team members
            team = random.sample(game.players, team_size)
            
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
            
            for player in game.players:
                # Simple strategy: good players are more likely to approve teams with more good players
                # Evil players are more likely to approve teams with more evil players
                team = game.get_current_quest().team
                good_count = sum(1 for p in team if p.team == Team.GOOD)
                evil_count = len(team) - good_count
                
                if player.team == Team.GOOD:
                    approve_probability = 0.5 + (good_count / len(team)) * 0.3
                else:
                    approve_probability = 0.4 + (evil_count / len(team)) * 0.4
                
                vote = VoteType.APPROVE if random.random() < approve_probability else VoteType.REJECT
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
                # Simple strategy: good players always vote success, evil players sometimes fail
                if player.team == Team.GOOD:
                    vote = VoteType.SUCCESS
                else:
                    # Evil players might choose to pass a quest for strategic reasons
                    vote_fail_probability = 0.7  # 70% chance to fail the quest
                    vote = VoteType.FAIL if random.random() < vote_fail_probability else VoteType.SUCCESS
                
                quest_votes[player] = vote
                game.vote_on_quest(player, vote)
            
            # Determine the result
            result = quest.process_result()
            
            print(f"Quest {game.current_quest_idx + 1} {result.value}!")
            
            # To maintain secrecy, only show the count of fail votes, not who voted fail
            fail_count = sum(1 for v in quest_votes.values() if v == VoteType.FAIL)
            print(f"There were {fail_count} fail votes.")
            
            # Log quest result
            log_game_event(logger, "quest_result", {
                "quest_number": game.current_quest_idx + 1,
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
    
    # Log game end
    log_game_event(logger, "game_end", {
        "winner": winner.value,
        "succeeded_quests": game.succeeded_quests,
        "failed_quests": game.failed_quests
    })
    
    # Save final game state
    save_game_state(game.get_game_state(), game_id)


if __name__ == "__main__":
    run_simple_game()