from typing import Dict, Optional, List, Tuple
import random
import textarena as ta
import re
import ast

class TakEnv(ta.Env):
    """
    Tak environment.
    """
    def __init__(
        self,
        difficulty: Optional[str] = "easy",
    ):
        """
        Initializa the Tak game environment
        
        Args:
            difficulty: Difficulty of the game. Can be "easy", "medium", "hard".
        """
        self.environment_name = "Tak"
        self.difficulty = difficulty

        # Initialize the gamm setting the board size
        if self.difficulty == "easy":
            self.board_size = 4
            self.stones = 15
            self.capstones = 0
        elif self.difficulty == "medium":
            self.board_size = 5
            self.stones = 21
            self.capstones = 1
        elif self.difficulty == "hard":
            self.board_size = 6
            self.stones = 30
            self.capstones = 1
        else:
            raise ValueError("Invalid difficulty level. Choose between 'easy', 'medium', 'hard'.")
        
        self.state = ta.State(
            num_players=2,
            max_turns=None,
            render_keys=["rendered_board"],
        )

    def reset(
        self,
        seed: Optional[int] = None,
    ) -> Optional[ta.Observations]:
        """
        Reset the environment to set a new game.
        
        Args:
            seed: Seed for the random number generator.
            
        Returns:
            Observations: Initial observations for the players.
        """
        ## set the random seed
        if seed is not None:
            random.seed(seed)
        else:
            random.seed()

        ## initialize the board
        self.board = self._generate_board()
        self.players = {
            0: {
                "stones": self.stones,
                "capstones": self.capstones
            },
            1: {
                "stones": self.stones,
                "capstones": self.capstones
            }
        }

        ## return the initial observations
        return self.state.reset(
            game_state = {
                "board": self.board,
                "rendered_board": self._render_board(),
            },
            player_prompt_function=self._generate_player_prompt
        )
    
    def _generate_board(self):
        """
        Generate the initial board state.
        """
        board = [[[] for _ in range(self.board_size)] for _ in range(self.board_size)]
        return board

    def _render_board(self):
        """
        Renders the board as a string and returns it.
        """
        # Calculate the maximum cell width across the board
        max_cell_width = max(
            len(self._format_stack(cell)) for row in self.board for cell in row
        )
        cell_width = max(max_cell_width, 5)  # Ensure minimum cell width for readability

        # Create the column headers
        header = "      " + "   ".join(f"{i:^{cell_width}}" for i in range(self.board_size))

        # Create the separator line
        separator = "     " + "-" * (self.board_size * (cell_width + 3) - 1)

        # Create rows
        rows = []
        for row_idx, row in enumerate(self.board):
            # Format each cell and align it
            row_display = [self._pad_cell(self._format_stack(cell), cell_width) for cell in row]
            rows.append(f"{row_idx:>3} | " + " | ".join(row_display) + " |")
            rows.append(separator)

        # Combine header, separator, and rows into a single string
        board_string = "\n".join([header, separator] + rows)
        return board_string


    def _format_stack(self, stack):
        """
        Helper function to format stacks in each cell,
        """
        if not stack:
            return ""  # Empty cell
        return f"({len(stack)}){'/'.join(stack)}"  # Full stack representation
    
    ## Helper function to pad cells for uniform display
    def _pad_cell(self, content, cell_width):
        return content.center(cell_width)

    ## Helper function to generate the player prompt
    def _generate_player_prompt(self, player_id):
        """
        Generate the player prompt.
        """
        prompt = (
            f"You are Player {player_id}. You are playing the Tak game.\n"
            "Your goal is to connect two opposite edges of the board with your pieces to form a road while blocking your opponent from doing the same.\n"
            "You can perform the following actions on your turn:\n"
            "- Place a piece on an empty square.\n"
            "- Move a stack of pieces from one square to one or more squares. You can stack your pieces on top of other pieces on the target square. The topmost piece determines ownership of the stack.\n"
            "- Split a stack of pieces into two or more stacks and distribute them to adjacent squares.\n"
            "- Flatten a wall stone into a flat stone using your capstone.\n"
            "- Place a Capstone on an empty square.\n"
            "- Move a Capstone from one square to one or more squares. A capstone can also flatten a wall stone during its move.\n"
            "\n"
            "For each move, submit your action using the format:\n"
            "[ACTION SOURCE ALLOCATION]\n"
            "- ACTION: The type of move you are making ('place' or 'move').\n"
            "- SOURCE: The grid coordinates where the stones originate. Use () for 'place'.\n"
            "- ALLOCATION: A dictionary where keys are target grid coordinates and values are the stones or pieces being moved or placed.\n"
            "\n"
            "Stone Types and Their Abilities:\n"
            "- Flat Stone ('F'):\n"
            "  - Forms part of a road (used to connect edges of the board).\n"
            "  - Can be stacked on top of other pieces or have other pieces stacked on it.\n"
            "  - Can be moved as part of a stack or individually.\n"
            "\n"
            "- Wall Stone ('W'):\n"
            "  - Blocks roads and prevents opponents from completing their connections.\n"
            "  - Cannot be part of a road.\n"
            "  - Can be flattened into a flat stone by a capstone.\n"
            "\n"
            "- Capstone ('C'):\n"
            "  - Acts as a flat stone and can form part of a road.\n"
            "  - Can flatten wall stones, removing their blocking effect.\n"
            "  - Cannot be covered by other pieces, always remains on top of the stack.\n"
            "  - Is a powerful tool for both road-building and disrupting your opponent's plans.\n"
            "\n"
            "The stones will be identified by the player as follows:\n"
            "- Flat Stone for Player 0: 'F0'\n"
            "- Wall Stone for Player 1: 'W1'\n"
            "- Capstone for Player 1: 'C1'\n"
            "\n"
            "Examples:\n"
            "- To place a capstone on (3,2):\n"
            "  [place () {'(3,2)': ['C0']}]\n"
            "- To move all pieces from (2,2) to (2,3):\n"
            "  [move (2,2) {'(2,3)': ['F0']}]\n"
            "- To split a stack of 5 pieces from (2,2) into two squares:\n"
            "  [move (2,2) {'(2,3)': ['F0', 'F0'], '(2,4)': ['W0', 'F0', 'C0']}]\n"
            "- To move and stack one piece from (2,2) onto an existing stack at (2,3):\n"
            "  [move (2,2) {'(2,3)': ['F0']}]\n"
            "\n"
            "When submitting your move, think strategically about your road-building goals and your opponent's potential moves.\n"
            "Here is the current board:\n"
            f"{self.board}\n"
        )

        return prompt


    def step(
        self,
        player_id: int,
        action: str,
    ) -> Tuple[
        Optional[ta.Observations],
        Optional[ta.Rewards],
        bool,
        bool,
        Optional[ta.Info]
    ]:
        """
        Execute the action for the player.
        
        Args:
            player_id: ID of the player.
            action: Action taken by the player.
            
        Returns:
            Observations: Observations for the next player.
            Rewards: Rewards for the player.
            Done: Whether the game is over.
            Info: Additional information.
        """
        ## check if the action is valid
        ## TODO - do we need to?

        ## Update the observation
        self.state.add_observation(
            from_id=player_id,
            to_id=-1, ## broadcasting to all players
            message=action,
            for_logging=True
        )

        ## action search pattern
        action_search_pattern = re.compile(
            r"\[(place|move)\s"                # Match action: "place" or "move"
            r"\((\d+,\d+|\s*)\)\s"            # Match source: "(row,col)" or "()"
            r"({.*?})\]"                      # Match allocation dictionary
        )  # Example: [move (2,2) {'(2,3)': ['F0', 'W0'], '(2,4)': ['C1']}]
        match = action_search_pattern.search(action)

        if not match:
            ## no matching action
            self.state.set_invalid_move(
                player_ids=[player_id],
                reasons=[f"Invalid move format. Player {player_id} did not respond with a valid move in square brackets."]
            )
        
        else:
            ## found the matching action
            action, source, allocation = self.extract_values(match.groups())

            if action == "place":
                ## place a piece on an empty square
                if not self._is_valid_placement(allocation):
                    ## invalid placement
                    self.state.set_invalid_move(
                        player_ids=[player_id],
                        reasons=[f"Invalid placement. Player {player_id} tried to place a piece on an invalid square."]
                    )
                else:
                    ## valid placement
                    row, col = list(allocation.keys())[0]
                    piece = list(allocation.values())[0]
                    # piece = [p.upper() + f"{player_id}" for p in piece]
                    self.board[row][col].extend(piece)
                    self._update_pieces(player_id, piece)

            elif action == "move":
                ## move a stack of pieces from one square to another
                if not self._is_valid_movement(source, allocation):
                    ## invalid movement
                    self.state.set_invalid_move(
                        player_ids=[player_id],
                        reasons=[f"Invalid movement. Player {player_id} tried to move pieces in an invalid way."]
                    )
                else:
                    ## valid movement
                    source_row, source_col = source
                    source_stack = self.board[source_row][source_col]
                    for target, pieces in allocation.items():
                        target_row, target_col = target
                        # pieces = [p.upper() + f"{player_id}" for p in pieces]
                        self.board[target_row][target_col].extend(pieces)
                        self.board[source_row][source_col] = source_stack[:-len(pieces)]

            else:
                ## invalid action
                self.state.set_invalid_move(
                    player_ids=[player_id],
                    reasons=[f"Invalid action. Player {player_id} tried to perform an unknown action."]
                )

            ## update the rendered board
            self.state.game_state["rendered_board"] = self._render_board()

        ## check if the game is over
        if self._check_win(player_id):
            ## game is over
            self.state.set_winners(
                player_ids=[player_id],
                reason=f"Player {player_id} has connected two opposite edges of the board."
            )
        
        return self.state.step()

    def _check_win(self, player_id):
        """
        Check if the specified player has won by forming a continuous road
        connecting two opposite edges of the board.

        Args:
            player_id: The ID of the player to check.

        Returns:
            bool: True if the player has won, False otherwise.
        """
        visited = set()
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Right, Down, Left, Up

        def is_valid_cell(row, col):
            """Check if the cell is valid for the player."""
            if 0 <= row < self.board_size and 0 <= col < self.board_size:
                stack = self.board[row][col]
                return stack and stack[-1].endswith(str(player_id))  # Top piece matches player ID
            return False

        def dfs(row, col, edge_reached):
            """Depth-first search to check for a continuous road."""
            if (row, col) in visited:
                return False
            visited.add((row, col))

            # Check if the current cell touches the opposite edge
            if edge_reached == "top" and row == self.board_size - 1:
                return True
            if edge_reached == "left" and col == self.board_size - 1:
                return True

            # Explore neighboring cells
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                print('new given row and col', new_row, new_col)
                if is_valid_cell(new_row, new_col):
                    if dfs(new_row, new_col, edge_reached):
                        return True

            return False

        # Check connections from the top edge to the bottom edge
        for col in range(self.board_size):
            if is_valid_cell(0, col):  # Start from the top edge
                if dfs(0, col, "top"):
                    return True

        # Check connections from the left edge to the right edge
        for row in range(self.board_size):
            if is_valid_cell(row, 0):  # Start from the left edge
                if dfs(row, 0, "left"):
                    return True

        return False


    def _update_pieces(self, player_id, piece):
        """
        Update the player's piece count if a new piece is placed.
        """
        if piece == ["F"] or piece == ["W"]:
            self.players[player_id]["stones"] -= 1
        else:
            self.players[player_id]["capstones"] -= 1
    
    def extract_values(self, matched_groups):
        """
        Extract and process the matched groups from the action string.
        
        Args:
            matched_groups: Tuple of matched groups from the action string.
            
        Returns:
            Tuple: Processed action, source, and allocation values.
        """
        action, source, allocation = matched_groups
    
        # Process source: Convert to a tuple of integers or None
        if source.strip():
            source = tuple(map(int, source.split(',')))  # Convert "row,col" to (row, col)
        else:
            source = None  # For place actions with no source

        # Process allocation: Check if allocation is in valid format
        if allocation.startswith("{") and allocation.endswith("}"):
            allocation_dict = ast.literal_eval(allocation)  # Safely parse the allocation
            # Convert keys to tuples of integers
            allocation_dict = {
                tuple(map(int, k.strip("()").split(','))): v
                for k, v in allocation_dict.items()
            }
        else:
            return None, None, None

        # Return processed values
        return action, source, allocation_dict


    def _is_valid_placement(
        self,
        allocation,
    ):
        """
        Check if the placement is valid.
        """
        allocation_keys = list(allocation.keys())
        allocation_values = list(allocation.values())
        if len(allocation_keys) > 1:
            ## needs to be a single allocation
            return False
        row, col = allocation_keys[0]
        piece = allocation_values[0]
        if not (0 <= row < self.board_size and 0 <= col < self.board_size):
            ## needs to be within the board
            return False
        if self.board[row][col]:
            ## needs to be an empty square
            return False
        if len(piece) > 1:
            ## needs to be a single piece
            return False
        return True
    
    def _is_valid_movement(
            self,
            source,
            allocation,
        ):
        """
        Check if the movement is valid.
        """

        ## check if the source stone is a cornerstone, flatstone, or wallstone
        stone_type = self.board[source[0]][source[1]][-1][0] ## get the type of the stone, F, W, or C

        if source is None:
            # Source must be provided
            return False

        if source[0] >= self.board_size or source[1] >= self.board_size:
            # Source must be within the board
            return False

        if not self.board[source[0]][source[1]]:
            # Source must have pieces
            return False
        
        if self.board[source[0]][source[1]][-1][-1] != str(self.state.get("current_player")):
            # Source must have the current player's stone on top
            return False

        # Get the source stack
        source_stack = self.board[source[0]][source[1]]

        # Flatten the allocated pieces in the order they are specified
        allocated_pieces = []
        for target, pieces in allocation.items():
            if target[0] >= self.board_size or target[1] >= self.board_size:
                # Target must be within the board
                return False
            if stone_type == "F" and "W" in self.board[target[0]][target[1]]:
                # Flat stones cannot be moved with wall stones
                return False
            if stone_type == "W" and "C" in self.board[target[0]][target[1]]:
                # Wall stones cannot be moved with capstones
                return False
            if stone_type == "C" and "W" in self.board[target[0]][target[1]]:
                # Capstones can flatten wall stones
                target_list = self.board[target[0]][target[1]]
                # replace the wall stone with a flat stone in the target list
                target_list[-1] = "F" + target_list[-1][1]
            if "C" in pieces and len(pieces) > 1:
                # Capstones cannot be moved with other pieces
                return False
            allocated_pieces.extend(pieces)

        # Ensure that the number of allocated pieces doesn't exceed the source stack size
        if len(allocated_pieces) > len(source_stack):
            return False

        # Validate that the allocated pieces match the top of the source stack
        top_of_stack = source_stack[-len(allocated_pieces):]  # Last `len(allocated_pieces)` elements
        if allocated_pieces != top_of_stack:
            # Allocated pieces must match the top of the stack in order
            return False

        return True

    def render(self):
        """
        Render the current state of the environment.
        """
        print(self.state.game_state["rendered_board"])

