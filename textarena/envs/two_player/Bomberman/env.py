import random
from typing import Any, Dict, List, Optional, Tuple, Set

import textarena as ta


class TwoPlayerBombermanEnv(ta.Env):
    """Environment for Two-Player Turn-Based Bomberman Game with Simultaneous Moves"""
    
    def __init__(
        self,
        grid_size: Optional[Tuple[int, int]] = (10, 10),
        max_turns: Optional[int] = 50,
        bomb_timer: Optional[int] = 2,
        explosion_radius: Optional[int] = 2
    ):
        """
        Initialize the Two-Player Bomberman environment.

        Args:
            grid_size (Tuple[int, int]): Dimensions of the grid (rows, cols).
            max_turns (int): Maximum number of turns before game ends in a draw.
            bomb_timer (int): Number of turns before a bomb explodes.
            explosion_radius (int): Distance of explosion in each direction.
        """
        self.grid_size = grid_size
        self.max_turns = max_turns
        self.bomb_timer = bomb_timer
        self.explosion_radius = explosion_radius
        
        # ASCII art representations
        self.symbols = {
            "empty": "  ",
            "player0": "P0",
            "player1": "P1",
            "indestructible_wall": "##",
            "destructible_wall": "[]",
            "bomb": "BB",
            "explosion": "XX"
        }
        
        # Initialize game state
        self.state = ta.State(
            num_players=2,
            max_turns=max_turns,
        )

    @property
    def terminal_render_keys(self):
        return ["grid", "player_positions", "bombs", "turn_count", "winner"]

    def _initialize_grid(self) -> List[List[str]]:
        """
        Initialize the game grid with walls and empty spaces.

        Returns:
            List[List[str]]: The initialized grid.
        """
        rows, cols = self.grid_size
        grid = [[self.symbols["empty"] for _ in range(cols)] for _ in range(rows)]
        
        # Place indestructible walls (every other row/col forms a grid pattern)
        for i in range(0, rows, 2):
            for j in range(0, cols, 2):
                grid[i][j] = self.symbols["indestructible_wall"]
        
        # Place destructible walls randomly (about 25% of remaining spaces)
        empty_cells = [(i, j) for i in range(rows) for j in range(cols) 
                       if grid[i][j] == self.symbols["empty"]]
        num_destructible = len(empty_cells) // 4
        destructible_positions = random.sample(empty_cells, num_destructible)
        for i, j in destructible_positions:
            grid[i][j] = self.symbols["destructible_wall"]
        
        return grid

    def _place_players(self, grid: List[List[str]]) -> Dict[int, Tuple[int, int]]:
        """
        Place players in opposite corners of the grid.

        Args:
            grid (List[List[str]]): The game grid.

        Returns:
            Dict[int, Tuple[int, int]]: Player positions.
        """
        rows, cols = self.grid_size
        player_positions = {
            0: (0, 0),  # Top-left corner
            1: (rows - 1, cols - 1)  # Bottom-right corner
        }
        
        # Ensure starting positions are clear
        for player_id, (i, j) in player_positions.items():
            while grid[i][j] != self.symbols["empty"]:
                if player_id == 0:
                    i += 1 if i + 1 < rows else 0
                    j += 1 if j + 1 < cols else 0
                else:
                    i -= 1 if i - 1 >= 0 else 0
                    j -= 1 if j - 1 >= 0 else 0
                player_positions[player_id] = (i, j)
            grid[i][j] = self.symbols[f"player{player_id}"]
        
        return player_positions

    def _render_grid(self, grid: List[List[str]]) -> str:
        """
        Render the grid as an ASCII art string.

        Args:
            grid (List[List[str]]): The game grid.

        Returns:
            str: ASCII representation of the grid.
        """
        return "\n".join([" ".join(row) for row in grid])

    def reset(self, seed: Optional[int] = None):
        """
        Reset the Bomberman game to its initial state.

        Args:
            seed (Optional[int]): Seed for reproducibility.

        Returns:
            Optional[ta.Observations]: Initial observations for both players.
        """
        if seed is not None:
            random.seed(seed)
        
        # Initialize grid and players
        grid = self._initialize_grid()
        player_positions = self._place_players(grid)
        
        self.state.reset(
            game_state={
                "grid": grid,
                "player_positions": player_positions,
                "bombs": [],  # List of (row, col, timer, owner_id)
                "turn_count": 0,
                "winner": None,
                "pending_actions": {},  # Store pending actions from players
                "round_complete": False  # Flag to track if the round is complete
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
        
        # Only show grid on first turn or after both players have moved
        if game_state["turn_count"] == 0 or game_state["round_complete"]:
            prompt = (
                f"Welcome to Two-Player Bomberman! You are Player {player_id} ({self.symbols[f'player{player_id}']}).\n"
                f"Round {game_state['turn_count'] // 2 + 1}/{self.max_turns // 2}\n\n"
                f"Current Grid:\n{grid_str}\n\n"
                f"Your position: ({pos[0]}, {pos[1]})\n"
                "ACTIONS:\n"
                "- Move: 'up', 'down', 'left', 'right'\n"
                "- Place Bomb: 'bomb'\n"
                "- Stay: 'stay'\n\n"
                "Enter your action:"
            )
        else:
            # Don't show grid while waiting for both players
            prompt = (
                f"Player {player_id}, it's your turn.\n"
                f"Round {game_state['turn_count'] // 2 + 1}/{self.max_turns // 2}\n\n"
                f"Your position: ({pos[0]}, {pos[1]})\n"
                "ACTIONS:\n"
                "- Move: 'up', 'down', 'left', 'right'\n"
                "- Place Bomb: 'bomb'\n"
                "- Stay: 'stay'\n\n"
                "Enter your action:"
            )
        return prompt

    def _is_valid_move(self, grid: List[List[str]], new_pos: Tuple[int, int]) -> bool:
        """
        Check if a move is valid.

        Args:
            grid (List[List[str]]): The game grid.
            new_pos (Tuple[int, int]): The target position.

        Returns:
            bool: True if move is valid, False otherwise.
        """
        rows, cols = self.grid_size
        row, col = new_pos
        if not (0 <= row < rows and 0 <= col < cols):
            return False
        cell = grid[row][col]
        return cell in [self.symbols["empty"], self.symbols["explosion"]]

    def _process_bombs(self, grid: List[List[str]], player_positions: Dict[int, Tuple[int, int]]) -> Set[int]:
        """
        Update bomb timers and process explosions.

        Args:
            grid (List[List[str]]): The game grid.
            player_positions (Dict[int, Tuple[int, int]]): Player positions.

        Returns:
            Set[int]: Set of player IDs that were hit by explosions.
        """
        rows, cols = self.grid_size
        bombs = self.state.game_state["bombs"]
        new_bombs = []
        explosion_cells = set()
        players_hit = set()
        
        # Update timers and detect explosions
        for bomb in bombs:
            row, col, timer, owner_id = bomb
            timer -= 1
            if timer > 0:
                new_bombs.append((row, col, timer, owner_id))
            else:
                # Bomb explodes
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, down, left, right
                explosion_cells.add((row, col))
                for dr, dc in directions:
                    for r in range(1, self.explosion_radius + 1):
                        new_row, new_col = row + dr * r, col + dc * r
                        if not (0 <= new_row < rows and 0 <= new_col < cols):
                            break
                        if grid[new_row][new_col] == self.symbols["indestructible_wall"]:
                            break
                        explosion_cells.add((new_row, new_col))
                        if grid[new_row][new_col] == self.symbols["destructible_wall"]:
                            break
        
        # Update grid with explosions
        for row, col in explosion_cells:
            if grid[row][col] == self.symbols["destructible_wall"]:
                grid[row][col] = self.symbols["empty"]
            else:
                grid[row][col] = self.symbols["explosion"]
        
        # Check for player hits
        for player_id, pos in player_positions.items():
            if pos in explosion_cells:
                players_hit.add(player_id)
        
        # Clear explosion markers after this turn
        for row, col in explosion_cells:
            if grid[row][col] == self.symbols["explosion"]:
                grid[row][col] = self.symbols["empty"]
        
        self.state.game_state["bombs"] = new_bombs
        return players_hit

    def _execute_actions(self):
        """
        Execute both players' actions once they are both received.
        """
        grid = self.state.game_state["grid"]
        player_positions = self.state.game_state["player_positions"]
        pending_actions = self.state.game_state["pending_actions"]
        
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
            elif action == "bomb":
                self.state.game_state["bombs"].append((row, col, self.bomb_timer, player_id))
                if grid[row][col] == self.symbols["empty"]:  # Only place bomb if no one else put a bomb there
                    grid[row][col] = self.symbols["bomb"]
            
            # Update player position if moving
            if action in ["up", "down", "left", "right"]:
                if self._is_valid_move(grid, (new_row, new_col)):
                    player_positions[player_id] = (new_row, new_col)
        
        # Place players back on grid (might have moved)
        for player_id, (row, col) in player_positions.items():
            # Only place player if cell is empty
            if grid[row][col] == self.symbols["empty"]:
                grid[row][col] = self.symbols[f"player{player_id}"]
            # If collision, keep their positions but don't update grid representation
        
        # Process bombs and check for hits
        players_hit = self._process_bombs(grid, player_positions)
        self.state.game_state["turn_count"] += 1
        
        # Clear pending actions and mark round as complete
        self.state.game_state["pending_actions"] = {}
        self.state.game_state["round_complete"] = True
        
        return players_hit
        
    def step(self, action: str) -> Tuple[bool, ta.Info]:
        """
        Process a player's action in the game.

        Args:
            action (str): The player's action ('up', 'down', 'left', 'right', 'bomb', 'stay').

        Returns:
            tuple: Game state update information.
        """
        current_player = self.state.current_player_id
        
        # Validate action
        action = action.lower().strip()
        if action not in ["up", "down", "left", "right", "bomb", "stay"]:
            self.state.add_observation(
                from_id=-1,
                to_id=current_player,
                message="Invalid action! Use 'up', 'down', 'left', 'right', 'bomb', or 'stay'. Try again:"
            )
            return self.state.step()
        
        # Log the action
        self.state.add_observation(
            from_id=current_player,
            to_id=-1,
            message=f"Player {current_player}: {action}",
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
            self.state.add_observation(
                from_id=-1,
                to_id=other_player,
                message=(
                    f"Player {other_player}, it's your turn.\n"
                    f"Round {self.state.game_state['turn_count'] // 2 + 1}/{self.max_turns // 2}\n\n"
                    f"Your position: ({pos[0]}, {pos[1]})\n"
                    "ACTIONS:\n"
                    "- Move: 'up', 'down', 'left', 'right'\n"
                    "- Place Bomb: 'bomb'\n"
                    "- Stay: 'stay'\n\n"
                    "Enter your action:"
                )
            )
            return self.state.step()
        
        # Both players have moved, execute actions and update game state
        players_hit = self._execute_actions()
        
        # Check game end conditions
        if players_hit:
            if len(players_hit) == 2:
                # Both players hit
                self.state.add_observation(
                    from_id=-1,
                    to_id=-1,
                    message="Both players were caught in explosions! Game ends in a draw."
                )
                self.state.game_state["winner"] = None
                self.state.set_winners(player_ids=[0, 1], reason="Draw due to mutual elimination")
            else:
                # One player hit
                loser = players_hit.pop()
                winner = 1 - loser
                self.state.add_observation(
                    from_id=-1,
                    to_id=-1,
                    message=f"Player {loser} was caught in an explosion! Player {winner} wins!"
                )
                self.state.game_state["winner"] = winner
                self.state.set_winners(player_ids=[winner], reason=f"Player {winner} eliminated opponent")
            return self.state.step()
        
        # Check turn limit
        if self.state.game_state["turn_count"] >= self.max_turns:
            self.state.add_observation(
                from_id=-1,
                to_id=-1,
                message="Maximum turns reached! Game ends in a draw."
            )
            self.state.game_state["winner"] = None
            self.state.set_winners(player_ids=[0, 1], reason="Draw due to turn limit")
            return self.state.step()
        
        # Send updated board state to both players
        grid = self.state.game_state["grid"]
        grid_str = self._render_grid(grid)
        
        for player_id in range(2):
            pos = self.state.game_state["player_positions"][player_id]
            self.state.add_observation(
                from_id=-1,
                to_id=player_id,
                message=(
                    f"Round {self.state.game_state['turn_count'] // 2 + 1}/{self.max_turns // 2}\n\n"
                    f"Current Grid:\n{grid_str}\n\n"
                    f"Your position: ({pos[0]}, {pos[1]})\n"
                    "ACTIONS:\n"
                    "- Move: 'up', 'down', 'left', 'right'\n"
                    "- Place Bomb: 'bomb'\n"
                    "- Stay: 'stay'\n\n"
                    "Enter your action:"
                )
            )
        
        return self.state.step()
