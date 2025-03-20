# AI Agents for The Resistance: Avalon
The Resistance: Avalon is one of my favourite social deduction games. It is an awesome past-time at social gatherings, where my friends and I will spend up to hours racking our brain to win the game. In this project, I aim to build AI agents to play Avalon. I implement both rule-based and LLM agents to explore their performance and limitations. This is an interesting task as playing well in Avalon requires deception and reasoning, skills that are relatively new to LLMs.

If you have not played Avalon before, here's a quick overview.

## Overview
The Resistance: Avalon is a hidden-role game where players are secretly divided into two teams:
- **Good Team**: Merlin, Percival, and Loyal Servants
- **Evil Team**: Assassin, Morgana, and Minions

The game involves multiple quests where players must form teams, vote on those teams, and complete missions. The good team aims to succeed three quests, while the evil team has 3 ways to win:
- fail three quests
- assassinate Merlin at the end of the game
- fail the team formation vote 5 consecutive times

### Core Gameplay Elements
1. **Team Formation**: The designated leader proposes a team for the current quest.
2. **Team Voting**: All players vote to approve or reject the proposed team.
3. **Quest Execution**: Approved team members secretly vote on whether the quest succeeds or fails (only evil players can cause a quest to fail).
4. **Assassination**: If the good team succeeds three quests, the Assassin gets one chance to identify and eliminate Merlin, which would result in an evil team victory.

The game's complexity comes from the hidden information, deception, and the need to deduce other players' roles based on their actions and voting patterns.

## Game Engine
I developed a robust game engine to simulate Avalon games and evaluate agent performance. The engine implements:
- Complete game state tracking
- Role-specific abilities and information visibility (e.g. Merlin is aware of the identity of the evil team)
- Team proposal and voting mechanisms
- Quest execution logic
- Assassination phase

I used a mixture of Github Copilot, Cursor and Windsurf to develop the game engine. Suffice to say, it saved me a lot of time.

## Rule-Based Agents
The first iteration of AI players uses rule-based strategies with distinct behaviors for good and evil team members.

### Simple Agent v1

#### Team Proposal Strategies
- **Good Players**:
  - Prioritize including themselves and other known good roles (Merlin, Percival, Loyal Servants)
  - Fill remaining slots with random players if necessary
- **Evil Players**:
  - Ensure at least one known evil teammate (Assassin, Morgana, Minion) is on the team
  - Fill remaining slots with random players to avoid suspicion

#### Team Voting (Approve/Reject)
- **Good Players**:
  - Reject if the proposed team contains any visible evil players
  - Approve otherwise
- **Evil Players**:
  - More likely to approve if:
    - The team includes evil allies
  - Base approval probability starts at 30%, increasing with evil presence or previous failed team formation votes

#### Quest Voting (Success/Fail)
- **Good Players**:
  - Always vote Success
- **Evil Players**:
  - Vote Fail with increasing probability per quest (e.g., 50% in Quest 1, 60% in Quest 2, etc.)

#### Assassination (Evil Only – Assassin Role)
- Targets players who approved successful quests consistently, aiming to eliminate Merlin
- Scores players based on their approval votes for successful quests, then selects the highest scorer

### Performance Analysis
The rule-based agents showed a significant imbalance in performance, with the evil team winning 87% of games. This highlighted the need for more sophisticated good team strategies, leading to the development of LLM-based agents.

## LLM Agents
To improve agent performance, particularly for the good team, I implemented agents powered by Large Language Models (LLMs).

### Models Used
- DeepSeek v3 (with and without Chain of Thought prompting)
- DeepSeek r1

I picked these two models to keep the cost of inference lower. In addition, I wanted to test the utility of chain of thought prompting, and whether reasoning models can lead to better performance. However, due to the long inference time of reasoning agents, I only ran 20 games for them as opposed to 50 games for the standard chat models.

### Core Strategies
1. **Context-Aware Decision Making**: The agents construct detailed game state prompts that include:
   - Player's own role and team affiliation
   - Visible roles based on special abilities
   - Current game phase and quest status
   - Quest history including team compositions and voting patterns
   - Current leader information

2. **Role-Based Strategy Adaptation**: The agents tailor their approach based on the player's role:
   - Evil players strategically decide when to fail quests
   - Good players always succeed quests (hard-coded behavior)
   - The Assassin specifically analyzes game patterns to identify Merlin

3. **Team Proposal Logic**: When proposing teams, the agents analyze:
   - Current quest requirements
   - Previous voting patterns
   - Known or suspected player allegiances
   - Strategic team compositions that benefit their faction

4. **Voting Strategy**: The agents employ careful analysis when voting:
   - Evaluate proposed team compositions
   - Consider the game phase and failed votes count
   - Factor in knowledge of other players' roles when available

5. **Chain-of-Thought Reasoning**: The agents can use a chain-of-thought approach that:
   - Analyzes current game state
   - Considers role-specific objectives
   - Evaluates information visible about other players
   - Assesses impact of decisions on team strategy

6. **Fallback Mechanisms**: The agents include robust error handling by falling back to rule-based behavior when:
   - API calls fail
   - Responses can't be parsed correctly
   - Timeouts occur

7. **Response Logging**: The agents log all LLM interactions for training and analysis purposes, building a dataset of game decisions.

### Performance Results

| Agent Type                      | Good Team Win Rate | Evil Team Win Rate | Evil Wins by Failed Quests | Evil Wins by Assassination | Evil Wins by Failed Votes |
|--------------------------------|-------------------|-------------------|---------------------------|---------------------------|--------------------------|
| Simple Agent v1                | 13% (13/100)      | 87% (87/100)      | 90.8% (79/87)             | 9.2%  (8/87)              | 0%   (0/87)              |
| DeepSeek v3 (no CoT)           | 44% (22/50)       | 56% (28/50)       | 67.9% (19/28)             | 32.1% (9/28)              | 0.0% (0/28)              |
| DeepSeek v3 (with CoT)         | 48% (24/50)       | 52% (26/50)       | 65.4% (17/26)             | 34.6% (9/26)              | 0.0% (0/26)              |
| DeepSeek r1                    | 40.0% (8/20)      | 60.0% (12/20)     | 50.0% (6/12)              | 50.0% (6/12)              | 0.0% (0/12)              |

### Key Observations:

1. **Significant Improvement**: LLM agents dramatically improved the good team's win rate from 13% to nearly 50%.

2. **Chain of Thought Impact**: The addition of Chain of Thought prompting yielded a modest improvement in the good team's performance (44% → 48%).

3. **Assassination Success**: LLM agents as evil players were much more successful at assassinating Merlin (9.2% → 32-50%), indicating improved deduction capabilities.

4. **Quest Failure Rates**: The sharp drop in the percentage of evil wins by failed quests suggests that the good players with LLMs were more able to deduce who is an evil player, and hence not nominate those players for the quest.

5. **Runtime Performance**: DeepSeek r1 completed 20 games in approximately 118 minutes. This was considerably slower than the chat models, which completed 50 games in the same amount of time.