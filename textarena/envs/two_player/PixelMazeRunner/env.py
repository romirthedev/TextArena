import random
from typing import Any, Dict, List, Optional, Tuple, Set
import textarena as ta


class PixelMazeRunnerEnv(ta.Env):
    """Environment for PixelMazeRunner Game with Simultaneous Moves"""
    
    def __init__(
        self,
        grid_size: Optional[Tuple[int, int]] = (15, 15),
        max_turns: Optional[int] = 100,
        num_keys: Optional[int] = 3,
        num_traps: Optional[int] = 5,
        num_powerups: Optional[int] = 3,
        num_destructible: Optional[int] = 10
    ):
        """
        Initialize the PixelMazeRunner environment.

        Args:
            grid_size (Tuple[int, int]): Dimensions of the grid (rows, cols).
            max_turns (int): Maximum number of turns before game ends in a draw.
            num_keys (int): Number of keys to place in the maze.
            num_traps (int): Number of traps to place in the maze.
            num_powerups (int): Number of powerups to place in the maze.
            num_destructible (int): Number of destructible obstacles to place.
        """
        self.grid_size = grid_size
        self.max_turns = max_turns
        self.num_keys = num_keys
        self.num_traps = num_traps
        self.num_powerups = num_powerups
        self.num_destructible = num_destructible
        
        # ASCII art representations
        self.symbols = {
            "empty": "  ",
            "player0": "P1",
            "player1": "P2",
            "wall": "██",
            "destructible": "▓▓",
            "key": "🔑",
            "trap": "⊗ ",
            "powerup": "⚡",
            "exit": "🚪",
            "path": "· "
        }
        
        # Initialize game state
        self.state = ta.State(
            num_players=2,
            max_turns=max_turns,
        )

    @property
    def terminal_render_keys(self):
        return ["grid", "player_positions", "turn_count", "winner", "player_stats"]

    def _generate_maze(self) -> List[List[str]]:
        """
        Generate a maze using a recursive backtracking algorithm.
        
        Returns:
            List[List[str]]: The generated maze.
        """
        rows, cols = self.grid_size
        # Start with a grid full of walls
        grid = [[self.symbols["wall"] for _ in range(cols)] for _ in range(rows)]
        
        # Define the recursive backtracking function
        def carve_passage(x, y, grid):
            # Mark the current cell as a path
            grid[y][x] = self.symbols["empty"]
            
            # Directions: up, right, down, left
            directions = [(0, -2), (2, 0), (0, 2), (-2, 0)]
            random.shuffle(directions)
            
            for dx, dy in directions:
                new_x, new_y = x + dx, y + dy
                if (0 <= new_x < cols and 0 <= new_y < rows and 
                    grid[new_y][new_x] == self.symbols["wall"]):
                    # Carve the wall between the current cell and the new cell
                    grid[y + dy//2][x + dx//2] = self.symbols["empty"]
                    carve_passage(new_x, new_y, grid)
        
        # Start carving from an odd position (to ensure walls between paths)
        start_x, start_y = 1, 1
        carve_passage(start_x, start_y, grid)
        
        # Ensure the start and exit are accessible
        grid[0][0] = self.symbols["empty"]  # Start
        grid[rows-1][cols-1] = self.symbols["exit"]  # Exit
        
        # Make sure there's a path from start to exit
        # Clear any walls that might block the path
        grid[0][1] = self.symbols["empty"]
        grid[1][0] = self.symbols["empty"]
        grid[rows-1][cols-2] = self.symbols["empty"]
        grid[rows-2][cols-1] = self.symbols["empty"]
        
        return grid

    def _place_items(self, grid: List[List[str]]) -> Dict[str, List[Tuple[int, int]]]:
        """
        Place keys, traps, powerups, and destructible obstacles in the maze.
        
        Args:
            grid (List[List[str]]): The maze grid.
            
        Returns:
            Dict[str, List[Tuple[int, int]]]: Positions of items placed in the maze.
        """
        rows, cols = self.grid_size
        empty_cells = [(i, j) for i in range(rows) for j in range(cols) 
                       if grid[i][j] == self.symbols["empty"]]
        
        # Reserve start and exit cells
        start = (0, 0)
        exit_pos = (rows-1, cols-1)
        if start in empty_cells:
            empty_cells.remove(start)
        if exit_pos in empty_cells:
            empty_cells.remove(exit_pos)
        
        # Randomly place items
        item_positions = {
            "keys": [],
            "traps": [],
            "powerups": [],
            "destructibles": []
        }
        
        # Place keys
        if empty_cells and self.num_keys > 0:
            key_positions = random.sample(empty_cells, min(self.num_keys, len(empty_cells)))
            for pos in key_positions:
                i, j = pos
                grid[i][j] = self.symbols["key"]
                item_positions["keys"].append(pos)
                empty_cells.remove(pos)
        
        # Place traps
        if empty_cells and self.num_traps > 0:
            trap_positions = random.sample(empty_cells, min(self.num_traps, len(empty_cells)))
            for pos in trap_positions:
                i, j = pos
                grid[i][j] = self.symbols["trap"]
                item_positions["traps"].append(pos)
                empty_cells.remove(pos)
        
        # Place powerups
        if empty_cells and self.num_powerups > 0:
            powerup_positions = random.sample(empty_cells, min(self.num_powerups, len(empty_cells)))
            for pos in powerup_positions:
                i, j = pos
                grid[i][j] = self.symbols["powerup"]
                item_positions["powerups"].append(pos)
                empty_cells.remove(pos)
        
        # Place destructible obstacles
        if empty_cells and self.num_destructible > 0:
            destructible_positions = random.sample(empty_cells, min(self.num_destructible, len(empty_cells)))
            for pos in destructible_positions:
                i, j = pos
                grid[i][j] = self.symbols["destructible"]
                item_positions["destructibles"].append(pos)
                empty_cells.remove(pos)
        
        return item_positions

    def _render_grid(self, grid: List[List[str]]) -> str:
        """
        Render the grid as an ASCII art string.

        Args:
            grid (List[List[str]]): The maze grid.

        Returns:
            str: ASCII representation of the grid.
        """
        return "\n".join(["".join(row) for row in grid])

    def reset(self, seed: Optional[int] = None):
        """
        Reset the PixelMazeRunner game to its initial state.

        Args:
            seed (Optional[int]): Seed for reproducibility.

        Returns:
            Optional[ta.Observations]: Initial observations for both players.
        """
        if seed is not None:
            random.seed(seed)
        
        # Generate maze
        grid = self._generate_maze()
        
        # Place items
        item_positions = self._place_items(grid)
        
        # Set player positions
        player_positions = {
            0: (0, 0),  # Top-left corner
            1: (0, 0)   # Both players start at the same position
        }
        
        # Mark player positions
        grid[0][0] = self.symbols["player0"]  # Only show one player initially
        
        # Initialize player stats
        player_stats = {
            0: {"keys": 0, "powerups": [], "traps_hit": 0, "active_effects": {}},
            1: {"keys": 0, "powerups": [], "traps_hit": 0, "active_effects": {}}
        }
        
        # Initialize game state
        self.state.reset(
            game_state={
                "grid": grid,
                "player_positions": player_positions,
                "item_positions": item_positions,
                "player_stats": player_stats,
                "turn_count": 0,
                "winner": None,
                "pending_actions": {},
                "round_complete": True,
                "exit_position": (self.grid_size[0]-1, self.grid_size[1]-1)
            },
            player_prompt_function=self._generate_player_prompt
        )

    def _generate_player_prompt(self, player_id: int, game_state: Dict[str, Any]) -> str:
        """
        Generate the initial prompt for a player.

        Args:
            player_id (int): ID of the player (0 or 1).
            game_state (Dict[str, Any]): Current game state.

        Returns:
            str: Initial prompt for the player.
        """
        grid_str = self._render_grid(game_state["grid"])
        pos = game_state["player_positions"][player_id]
        player_stats = game_state["player_stats"][player_id]
        
        # Only show grid on first turn or after both players have moved
        if game_state["turn_count"] == 0 or game_state["round_complete"]:
            prompt = (
                f"Welcome to PixelMazeRunner! You are Player {player_id+1} ({self.symbols[f'player{player_id}']}).\n"
                f"Turn {game_state['turn_count'] + 1}/{self.max_turns}\n\n"
                f"Current Maze:\n{grid_str}\n\n"
                f"Your position: ({pos[0]}, {pos[1]})\n"
                f"Keys collected: {player_stats['keys']}\n"
                f"Traps hit: {player_stats['traps_hit']}\n"
                f"Active effects: {', '.join(player_stats['active_effects'].keys()) if player_stats['active_effects'] else 'None'}\n\n"
                "ACTIONS:\n"
                "- Move: 'up', 'down', 'left', 'right'\n"
                "- Stay: 'stay'\n\n"
                "Enter your action:"
            )
        else:
            # Don't show grid while waiting for both players
            prompt = (
                f"Player {player_id+1}, it's your turn.\n"
                f"Turn {game_state['turn_count'] + 1}/{self.max_turns}\n\n"
                f"Your position: ({pos[0]}, {pos[1]})\n"
                f"Keys collected: {player_stats['keys']}\n"
                f"Traps hit: {player_stats['traps_hit']}\n"
                f"Active effects: {', '.join(player_stats['active_effects'].keys()) if player_stats['active_effects'] else 'None'}\n\n"
                "ACTIONS:\n"
                "- Move: 'up', 'down', 'left', 'right'\n"
                "- Stay: 'stay'\n\n"
                "Enter your action:"
            )
        return prompt

    def _is_valid_move(self, grid: List[List[str]], new_pos: Tuple[int, int], player_id: int) -> bool:
        """
        Check if a move is valid.

        Args:
            grid (List[List[str]]): The maze grid.
            new_pos (Tuple[int, int]): The target position.
            player_id (int): ID of the player making the move.

        Returns:
            bool: True if move is valid, False otherwise.
        """
        rows, cols = self.grid_size
        row, col = new_pos
        
        # Check if position is within grid bounds
        if not (0 <= row < rows and 0 <= col < cols):
            return False
        
        cell = grid[row][col]
        
        # Check if position is not a wall
        if cell == self.symbols["wall"]:
            return False
        
        # Check if position is a destructible obstacle
        if cell == self.symbols["destructible"]:
            # Check if player has powerup that allows breaking obstacles
            player_stats = self.state.game_state["player_stats"][player_id]
            if "breaker" in player_stats["active_effects"]:
                return True
            return False
        
        # All other cells are valid moves
        return True

    def _process_player_interaction(self, player_id: int, position: Tuple[int, int], grid: List[List[str]]) -> Dict[str, Any]:
        """
        Process player interaction with the cell they moved to.

        Args:
            player_id (int): ID of the player.
            position (Tuple[int, int]): The player's new position.
            grid (List[List[str]]): The maze grid.

        Returns:
            Dict[str, Any]: Updated player stats and effects.
        """
        row, col = position
        cell = grid[row][col]
        player_stats = self.state.game_state["player_stats"][player_id].copy()
        messages = []
        
        # Process key collection
        if cell == self.symbols["key"]:
            player_stats["keys"] += 1
            grid[row][col] = self.symbols["empty"]
            messages.append(f"Player {player_id+1} found a key!")
            
            # Check if all keys have been collected
            if player_stats["keys"] == self.num_keys:
                messages.append(f"Player {player_id+1} has collected all keys!")
        
        # Process trap effects
        elif cell == self.symbols["trap"]:
            player_stats["traps_hit"] += 1
            grid[row][col] = self.symbols["empty"]
            
            # Apply trap effect (slow down player for 2 turns)
            player_stats["active_effects"]["slowed"] = 2
            messages.append(f"Player {player_id+1} hit a trap! Movement slowed for 2 turns.")
        
        # Process powerup collection
        elif cell == self.symbols["powerup"]:
            grid[row][col] = self.symbols["empty"]
            
            # Randomly assign a powerup effect
            powerup_types = ["speed", "breaker", "invulnerable"]
            powerup = random.choice(powerup_types)
            
            if powerup == "speed":
                player_stats["active_effects"]["speed"] = 3
                messages.append(f"Player {player_id+1} found a speed powerup! Extra move for 3 turns.")
            elif powerup == "breaker":
                player_stats["active_effects"]["breaker"] = 5
                messages.append(f"Player {player_id+1} found a breaker powerup! Can destroy obstacles for 5 turns.")
            elif powerup == "invulnerable":
                player_stats["active_effects"]["invulnerable"] = 3
                messages.append(f"Player {player_id+1} found an invulnerability powerup! Immune to traps for 3 turns.")
        
        # Process destructible obstacle
        elif cell == self.symbols["destructible"] and "breaker" in player_stats["active_effects"]:
            grid[row][col] = self.symbols["empty"]
            messages.append(f"Player {player_id+1} destroyed an obstacle!")
        
        # Process reaching the exit
        elif cell == self.symbols["exit"]:
            # Check if player needs keys to exit
            if self.num_keys > 0 and player_stats["keys"] < self.num_keys:
                messages.append(f"Player {player_id+1} reached the exit but needs all {self.num_keys} keys to win!")
            else:
                # Player has enough keys to exit
                self.state.game_state["winner"] = player_id
                messages.append(f"Player {player_id+1} reached the exit and won the game!")
        
        return {"player_stats": player_stats, "messages": messages}

    def _update_active_effects(self, player_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update active effects by decreasing their duration.

        Args:
            player_stats (Dict[str, Any]): The player's stats.

        Returns:
            Dict[str, Any]: Updated player stats.
        """
        updated_stats = player_stats.copy()
        effects_to_remove = []
        
        for effect, duration in updated_stats["active_effects"].items():
            # Decrease duration
            updated_stats["active_effects"][effect] = duration - 1
            
            # Remove effect if duration is 0
            if updated_stats["active_effects"][effect] <= 0:
                effects_to_remove.append(effect)
        
        # Remove expired effects
        for effect in effects_to_remove:
            del updated_stats["active_effects"][effect]
        
        return updated_stats

    def _execute_actions(self):
        """
        Execute both players' actions once they are both received.
        """
        grid = self.state.game_state["grid"]
        player_positions = self.state.game_state["player_positions"].copy()
        pending_actions = self.state.game_state["pending_actions"]
        player_stats = self.state.game_state["player_stats"]
        messages = []
        
        # Clear current player positions
        for player_id, (row, col) in player_positions.items():
            grid[row][col] = self.symbols["empty"]
        
        # Process actions for both players
        for player_id, action in pending_actions.items():
            row, col = player_positions[player_id]
            action = action.lower().strip()
            new_row, new_col = row, col
            
            if action == "up":
                new_row -= 1
            elif action == "down":
                new_row += 1
            elif action == "left":
                new_col -= 1
            elif action == "right":
                new_col += 1
            
            # Check if move is valid
            if action in ["up", "down", "left", "right"] and self._is_valid_move(grid, (new_row, new_col), player_id):
                player_positions[player_id] = (new_row, new_col)
        
        # Process player interactions with cells
        for player_id, position in player_positions.items():
            result = self._process_player_interaction(player_id, position, grid)
            self.state.game_state["player_stats"][player_id] = result["player_stats"]
            messages.extend(result["messages"])
        
        # Update active effects
        for player_id in range(2):
            self.state.game_state["player_stats"][player_id] = self._update_active_effects(
                self.state.game_state["player_stats"][player_id]
            )
        
        # Update grid with new player positions
        for player_id, (row, col) in player_positions.items():
            if grid[row][col] == self.symbols["empty"]:
                grid[row][col] = self.symbols[f"player{player_id}"]
        
        # Update game state
        self.state.game_state["player_positions"] = player_positions
        self.state.game_state["turn_count"] += 1
        
        # Clear pending actions and mark round as complete
        self.state.game_state["pending_actions"] = {}
        self.state.game_state["round_complete"] = True
        
        return messages

    def step(self, action: str) -> Tuple[bool, ta.Info]:
        """
        Process a player's action in the game.

        Args:
            action (str): The player's action ('up', 'down', 'left', 'right', 'stay').

        Returns:
            tuple: Game state update information.
        """
        current_player = self.state.current_player_id
        
        # Validate action
        action = action.lower().strip()
        if action not in ["up", "down", "left", "right", "stay"]:
            self.state.add_observation(
                from_id=-1,
                to_id=current_player,
                message="Invalid action! Use 'up', 'down', 'left', 'right', or 'stay'. Try again:"
            )
            return self.state.step()
        
        # Log the action
        self.state.add_observation(
            from_id=current_player,
            to_id=-1,
            message=f"Player {current_player+1}: {action}",
            for_logging=True
        )
        
        # Store the pending action
        self.state.game_state["pending_actions"][current_player] = action
        
        # Switch to other player if they haven't moved yet
        other_player = 1 - current_player
        
        # Check if both players have submitted actions
        if len(self.state.game_state["pending_actions"]) < 2:
            self.state.game_state["round_complete"] = False
            
            # Prompt the other player for their move
            pos = self.state.game_state["player_positions"][other_player]
            player_stats = self.state.game_state["player_stats"][other_player]
            
            self.state.add_observation(
                from_id=-1,
                to_id=other_player,
                message=(
                    f"Player {other_player+1}, it's your turn.\n"
                    f"Turn {self.state.game_state['turn_count'] + 1}/{self.max_turns}\n\n"
                    f"Your position: ({pos[0]}, {pos[1]})\n"
                    f"Keys collected: {player_stats['keys']}\n"
                    f"Traps hit: {player_stats['traps_hit']}\n"
                    f"Active effects: {', '.join(player_stats['active_effects'].keys()) if player_stats['active_effects'] else 'None'}\n\n"
                    "ACTIONS:\n"
                    "- Move: 'up', 'down', 'left', 'right'\n"
                    "- Stay: 'stay'\n\n"
                    "Enter your action:"
                )
            )
            return self.state.step()
        
        # Both players have moved, execute actions and update game state
        messages = self._execute_actions()
        
        # Broadcast any messages
        for message in messages:
            self.state.add_observation(
                from_id=-1,
                to_id=-1,
                message=message
            )
        
        # Check if we have a winner
        if self.state.game_state["winner"] is not None:
            winner = self.state.game_state["winner"]
            self.state.add_observation(
                from_id=-1,
                to_id=-1,
                message=f"Game Over! Player {winner+1} wins by reaching the exit!"
            )
            self.state.set_winners(player_ids=[winner], reason=f"Player {winner+1} reached the exit")
            return self.state.step()
        
        # Check turn limit
        if self.state.game_state["turn_count"] >= self.max_turns:
            # Determine winner based on closest to exit
            exit_pos = self.state.game_state["exit_position"]
            distances = {}
            for player_id, pos in self.state.game_state["player_positions"].items():
                distances[player_id] = abs(pos[0] - exit_pos[0]) + abs(pos[1] - exit_pos[1])
            
            # Find player closest to exit
            closest_player = min(distances, key=distances.get)
            
            # Check if it's a tie
            if list(distances.values()).count(distances[closest_player]) > 1:
                self.state.add_observation(
                    from_id=-1,
                    to_id=-1,
                    message="Maximum turns reached! Both players are equidistant from the exit. Game ends in a draw."
                )
                self.state.game_state["winner"] = None
                self.state.set_winners(player_ids=[0, 1], reason="Draw due to turn limit")
            else:
                self.state.add_observation(
                    from_id=-1,
                    to_id=-1,
                    message=f"Maximum turns reached! Player {closest_player+1} wins by being closest to the exit."
                )
                self.state.game_state["winner"] = closest_player
                self.state.set_winners(player_ids=[closest_player], reason=f"Player {closest_player+1} was closest to exit")
            
            return self.state.step()
        
        # Send updated board state to both players
        grid = self.state.game_state["grid"]
        grid_str = self._render_grid(grid)
        
        for player_id in range(2):
            pos = self.state.game_state["player_positions"][player_id]
            player_stats = self.state.game_state["player_stats"][player_id]
            
            self.state.add_observation(
                from_id=-1,
                to_id=player_id,
                message=(
                    f"Turn {self.state.game_state['turn_count'] + 1}/{self.max_turns}\n\n"
                    f"Current Maze:\n{grid_str}\n\n"
                    f"Your position: ({pos[0]}, {pos[1]})\n"
                    f"Keys collected: {player_stats['keys']}\n"
                    f"Traps hit: {player_stats['traps_hit']}\n"
                    f"Active effects: {', '.join(player_stats['active_effects'].keys()) if player_stats['active_effects'] else 'None'}\n\n"
                    "ACTIONS:\n"
                    "- Move: 'up', 'down', 'left', 'right'\n"
                    "- Stay: 'stay'\n\n"
                    "Enter your action:"
                )
            )
        
        return self.state.step()
