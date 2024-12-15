from typing import Optional, Dict, Tuple, List, Any
import random
import textarena as ta
import re

class StrategoEnv(ta.Env):
    """
    A two-player implementation of the board game Stratego.
    """
    def __init__(
        self
    ):
        """
        Initialize the environment.
        """
        self.environment_name = "Stratego"

        ## initialise the state
        self.state = ta.State(
            num_players=2,
            max_turns=None
        )

        ## set up the board items
        self.piece_counts = {
            'Flag': 1, 'Bomb': 6, 'Spy': 1, 'Scout': 8, 'Miner': 5,
            'Sergeant': 4, 'Lieutenant': 4, 'Captain': 4, 'Major': 3,
            'Colonel': 2, 'General': 1, 'Marshal': 1
        }
        self.piece_ranks = {
            'Flag': 0, 'Bomb': 11, 'Spy': 1, 'Scout': 2, 'Miner': 3,
            'Sergeant': 4, 'Lieutenant': 5, 'Captain': 6, 'Major': 7,
            'Colonel': 8, 'General': 9, 'Marshal': 10
        }
        self.lakes = [(4, 2), (4, 3), (5, 2), (5, 3), (4, 6), (4, 7), (5, 6), (5, 7)]
        self.player_pieces = {
            0: [],
            1: []
        }
        self.board = [[None for _ in range(10)] for _ in range(10)]

        ## add render objects
        # self.board_state_render = ta.envs.two_player.Stratego.render.BoardStateRender
        self.render_keys = ["rendered_board"]

    def reset(
        self,
        seed: Optional[int] = None
    ):
        """
        Reset the environment to start a new game.

        Args:
            seed (Optional[int]): The seed for the random number generator.
        """
        ## set the seed
        random.seed(seed)

        ## populate the board
        self.board = self._populate_board()

        ## initialise the game state
        self.state.reset(
            game_state={
                "board": self.board,
                "player_pieces": self.player_pieces,
                "rendered_board": self._render_board(player_id=None, full_board=True)
            },
            player_prompt_function=self._generate_player_prompt,
            seed=seed
        )
    
    def _generate_player_prompt(self, player_id: int, game_state: Dict[str, Any]):
        """
        Generates the player prompt for the current player.

        Args:
            player_id (int): The ID of the current player.
            game_state (Dict[str, Any]): The current game state.
        """
        prompt = (
            f"You are Player {player_id}. You are playing the Stratego game.\n"
            "Your goal is to capture your opponent's Flag or eliminate all of their movable pieces.\n"
            "At the start of the game, you have placed your army on the board, including your Flag, Bombs, and other pieces of varying ranks.\n"
            "On your turn, you can move one piece by only one step to an adjacent square (up, down, left, or right). For example, it can only move from A1 to B1. If your selected piece is a Bomb or a Flag, then they cannot be moved.\n"
            "If you move onto a square occupied by an opponent's piece, a battle will occur:\n"
            "- The piece with the higher rank wins and eliminates the opponent's piece.\n"
            "- If the ranks are equal, both pieces are removed.\n"
            "- Bombs eliminate most attacking pieces except Miners, which neutralize Bombs.\n"
            "- Spies can defeat the Marshal if they attack first but lose to any other piece.\n"
            "\n"
            "Your task is to plan your moves strategically:\n"
            "- Focus on identifying the ranks of your opponent's pieces through their movements and battles.\n"
            "- Protect your Flag while attempting to capture your opponent's Flag.\n"
            "- Use Scouts to gain information, as they can move multiple squares in a straight line. However, scouts cannot move jump over pieces. Example, if there is a piece in between the scout and the destination, the scout cannot move to the destination.\n"
            "\n"
            "To make a move, specify the coordinates of the piece you want to move and its destination in the format [A0 B0]. For example, to move a piece from row 0, column 0 to row 1, column 0, you would input [A0 B0].\n"
            "The board will show your pieces, their positions, and the known positions of your opponent's pieces, whilst not revealing the ranks of your opponent's pieces.\n"
            "Here is the current board state:\n"
        )

        prompt += self._render_board(player_id=player_id, full_board=False)

        return prompt

    
    def _populate_board(self):
        """
        Populates the board with pieces for each player.
        """

        ## set up the pieces for each player based on random placement
        for player in range(2):
            rows = range(0, 4) if player == 0 else range(6, 10)
            for piece, count in self.piece_counts.items():
                piece = piece.lower() if player == 0 else piece.upper()
                for _ in range(count):
                    while True:
                        row = random.choice(rows)
                        col = random.randint(0, 9)
                        if (row, col) in self.lakes or self.board[row][col] is not None:
                            continue
                        self.board[row][col] = {'rank': piece, 'player': player}
                        self.player_pieces[player].append((row, col))
                        break

        return self.board

    
    def _render_board(self, player_id, full_board: bool = False):
        """
        Renders the board state.

        Args:
            player_id (int): The player viewing the board.
            full_board (bool): Whether to render the full board or just the visible pieces.
        """
        res = []
        column_headers = "    " + "  ".join([str(i) for i in range(10)])
        res.append(column_headers + "\n")
        for row in range(10):
            row_label = chr(row + 65)  # Convert row index to a letter (A, B, C, ...)
            res.append(row_label + "  ")
            for col in range(10):
                if (row, col) in self.lakes:
                    res.append(" ~ ")
                elif self.board[row][col] is None:
                    res.append(" . ")
                else:
                    piece = self.board[row][col]
                    if full_board:
                        res.append(f" {piece['rank'][0]} ")
                    else:
                        if piece['player'] == player_id:
                            res.append(f" {piece['rank'][0]} ")
                        else:
                            res.append(" ? ")
            res.append("\n")

        return "".join(res)

    def step(
        self,
        action: str
    ):
        """
        Execute an action in the environment.

        Args:
            action (str): The action to be executed

        Returns:
            Rewards: Rewards for the players.
            bool: Whether the game is over.
            bool: Whether the turn is over.
            Info: Additional information.
        """
        player_id = self.state.current_player_id

        ## validate the action
        self.state.check_action_format(
            action=action,
        )

        ## update the observation
        self.state.add_observation(
            from_id=player_id,
            to_id=player_id, ## send the observation to the same player since this is a private observation
            message=action,
            for_logging=True
        )

        ## action search pattern
        action_search_pattern = re.compile(r"\[([A-J])([0-9]) ([A-J])([0-9])\]") ## e.g. [A1 B1]
        match = action_search_pattern.search(action)

        if match is None:
            self.state.set_invalid_move(
                player_ids=[player_id],
                reasons=[f"Invalid action format. Player {player_id} did not input a move in the format [A0 B0]."]
            )
        
        else:
            src_row, src_col, dest_row, dest_col = match.groups()
            source = f"{src_row}{src_col}"
            dest = f"{dest_row}{dest_col}"
            src_row, src_col = ord(src_row) - 65, int(src_col)
            dest_row, dest_col = ord(dest_row) - 65, int(dest_col)
             

            if not (0 <= src_row < 10 and 0 <= src_col < 10 and 0 <= dest_row < 10 and 0 <= dest_col < 10):
                self.state.set_invalid_move(
                    player_ids=[player_id],
                    reasons=[f"Invalid action format. Player {player_id} did not input valid coordinates."]
                )
            elif self.board[src_row][src_col] is None or self.board[src_row][src_col]['player'] != player_id:
                self.state.set_invalid_move(
                    player_ids=[player_id],
                    reasons=[f"Invalid action format. Player {player_id} must move one of their own pieces."]
                )
            elif self.board[src_row][src_col]['rank'].lower() == 'scout':
                ## check if there's a piece in between the source and destination
                if src_row == dest_row:
                    for col in range(min(src_col, dest_col) + 1, max(src_col, dest_col)):
                        if self.board[src_row][col] is not None:
                            self.state.set_invalid_move(
                                player_ids=[player_id],
                                reasons=[f"Invalid action format. Player {player_id} cannot move a scout through other pieces."]
                            )
                            break
                elif src_col == dest_col:
                    for row in range(min(src_row, dest_row) + 1, max(src_row, dest_row)):
                        if self.board[row][src_col] is not None:
                            self.state.set_invalid_move(
                                player_ids=[player_id],
                                reasons=[f"Invalid action format. Player {player_id} cannot move a scout through other pieces."]
                            )
                            break
            elif abs(src_row - dest_row) + abs(src_col - dest_col) != 1 and self.board[src_row][src_col]['rank'].lower() != 'scout':
                ## !  - by right, only scouts can move more than one square at a time but we are not implementing that yet
                self.state.set_invalid_move(
                    player_ids=[player_id],
                    reasons=[f"Invalid action format. Pieces can only move one square at a time."]
                )
            elif self.board[dest_row][dest_col] is not None and self.board[dest_row][dest_col]['player'] == player_id:
                self.state.set_invalid_move(
                    player_ids=[player_id],
                    reasons=[f"Invalid action format. Player {player_id} cannot move onto their own piece."]
                )
            elif (dest_row, dest_col) in self.lakes:
                self.state.set_invalid_move(
                    player_ids=[player_id],
                    reasons=[f"Invalid action format. Player {player_id} cannot move into the lake."]
                )
            else:
                attacking_piece = self.board[src_row][src_col]
                target_piece = self.board[dest_row][dest_col]

                if target_piece is None:
                    ## move to an empty square
                    self.board[dest_row][dest_col] = attacking_piece
                    self.board[src_row][src_col] = None
                    self.player_pieces[player_id].remove((src_row, src_col))
                    self.player_pieces[player_id].append((dest_row, dest_col))
                    
                    ## add the observation to both players separately
                    self.state.add_observation(
                        from_id=-1,
                        to_id=player_id,
                        message=(
                            f"You have moved your piece from {source} to {dest}. Here is the updated board state:\n"
                            f"{self._render_board(player_id=player_id, full_board=False)}"
                        ),
                        for_logging=False
                    )

                    self.state.add_observation(
                        from_id=-1,
                        to_id=1 - player_id,
                        message=(
                            f"Player {player_id} has moved a piece from {source} to {dest}. Here is the updated board state:\n"
                            f"{self._render_board(player_id=1 - player_id, full_board=False)}"
                        ),
                        for_logging=False
                    )

                else:
                    ## battle
                    attacking_rank = self.piece_ranks[attacking_piece['rank']]
                    target_rank = self.piece_ranks[target_piece['rank']]
                    if attacking_rank == target_rank:
                        ## both pieces are removed
                        self.board[src_row][src_col] = None
                        self.board[dest_row][dest_col] = None
                        self.player_pieces[player_id].remove((src_row, src_col))
                        self.player_pieces[1 - player_id].remove((dest_row, dest_col))

                        ## add the observation to both players separately
                        self.state.add_observation(
                            from_id=-1,
                            to_id=player_id,
                            message=(
                                f"You have moved your piece from {source} to {dest}. The attacking piece was {attacking_piece['rank']} and the destination piece was {target_piece['rank']}. As the ranks are the same, both pieces lost. Here is the updated board state:\n"
                                f"{self._render_board(player_id=player_id, full_board=False)}"
                            ),
                            for_logging=False
                        )

                        self.state.add_observation(
                            from_id=-1,
                            to_id=1 - player_id,
                            message=(
                                f"Player {player_id} has moved a piece from {source} to {dest}. The attacking piece was {attacking_piece['rank']} and the destination piece was {target_piece['rank']}. As the ranks are the same, both pieces lost. Here is the updated board state:\n"
                                f"{self._render_board(player_id=1 - player_id, full_board=False)}"
                            ),
                            for_logging=False
                        )

                    elif target_piece['rank'] == 'Bomb':
                        if attacking_piece['rank'] == 'Miner':
                            ## Miner defuses the bomb
                            self.board[dest_row][dest_col] = attacking_piece
                            self.board[src_row][src_col] = None
                            self.player_pieces[player_id].remove((src_row, src_col))
                            self.player_pieces[player_id].append((dest_row, dest_col))

                            ## add the observation to both players separately
                            self.state.add_observation(
                                from_id=-1,
                                to_id=player_id,
                                message=(
                                    f"You have moved your piece from {source} to {dest}. The attacking piece was {attacking_piece['rank']} and the destination piece was {target_piece['rank']}. As miners can defuse bombs, you won the battle. Here is the updated board state:\n"
                                    f"{self._render_board(player_id=player_id, full_board=False)}"
                                ),
                                for_logging=False
                            )

                            self.state.add_observation(
                                from_id=-1,
                                to_id=1 - player_id,
                                message=(
                                    f"Player {player_id} has moved a piece from {source} to {dest}. The attacking piece was {attacking_piece['rank']} and the destination piece was {target_piece['rank']}. As miners can defuse bombs, you lost the battle. Here is the updated board state:\n"
                                    f"{self._render_board(player_id=1 - player_id, full_board=False)}"
                                ),
                                for_logging=False
                            )

                        else:
                            ## attacking piece is destroyed
                            self.board[src_row][src_col] = None
                            self.player_pieces[player_id].remove((src_row, src_col))

                            ## add the observation to both players separately
                            self.state.add_observation(
                                from_id=-1,
                                to_id=player_id,
                                message=(
                                    f"You have moved your piece from {source} to {dest}. The attacking piece was {attacking_piece['rank']} and the destination piece was {target_piece['rank']}. As the attacker is not a miner, you lost the battle. Here is the updated board state:\n"
                                    f"{self._render_board(player_id=player_id, full_board=False)}"
                                ),
                                for_logging=False
                            )

                            self.state.add_observation(
                                from_id=-1,
                                to_id=1 - player_id,
                                message=(
                                    f"Player {player_id} has moved a piece from {source} to {dest}. The attacking piece was {attacking_piece['rank']} and the destination piece was {target_piece['rank']}. As the attacker is not a miner, you won the battle. Here is the updated board state:\n"
                                    f"{self._render_board(player_id=1 - player_id, full_board=False)}"
                                ),
                                for_logging=False
                            )

                    elif target_piece['rank'] == 'Flag':
                        ## game over
                        self.state.set_winners(
                            player_ids=[player_id],
                            reason=[f"Player {player_id} has captured the opponent's flag!"]
                        )
                    elif attacking_piece['rank'] == 'Spy' and target_piece['rank'] == 'Marshal':
                        ## Spy beats Marshal only if spy attacks first
                        self.board[dest_row][dest_col] = attacking_piece
                        self.board[src_row][src_col] = None
                        self.player_pieces[player_id].remove((src_row, src_col))
                        self.player_pieces[player_id].append((dest_row, dest_col))
                        self.player_pieces[1 - player_id].remove((dest_row, dest_col))

                        ## add the observation to both players separately
                        self.state.add_observation(
                            from_id=-1,
                            to_id=player_id,
                            message=(
                                f"You have moved your piece from {source} to {dest}. The attacking piece was {attacking_piece['rank']} and the destination piece was {target_piece['rank']}. As the attacker is a spy and the destination is a marshall, you won the battle. Here is the updated board state:\n"
                                f"{self._render_board(player_id=player_id, full_board=False)}"
                            ),
                            for_logging=False
                        )

                        self.state.add_observation(
                            from_id=-1,
                            to_id=1 - player_id,
                            message=(
                                f"Player {player_id} has moved a piece from {source} to {dest}. The attacking piece was {attacking_piece['rank']} and the destination piece was {target_piece['rank']}. As the attacker is a spy and the destination is a marshall, you lost the battle. Here is the updated board state:\n"
                                f"{self._render_board(player_id=1 - player_id, full_board=False)}"
                            ),
                            for_logging=False
                        )

                    elif attacking_rank > target_rank:
                        ## attacker wins
                        self.board[dest_row][dest_col] = attacking_piece
                        self.board[src_row][src_col] = None
                        self.player_pieces[player_id].remove((src_row, src_col))
                        self.player_pieces[player_id].append((dest_row, dest_col))
                        self.player_pieces[1 - player_id].remove((dest_row, dest_col))

                        ## add the observation to both players separately
                        self.state.add_observation(
                            from_id=-1,
                            to_id=player_id,
                            message=(
                                f"You have moved your piece from {source} to {dest}. The attacking piece was {attacking_piece['rank']} and the destination piece was {target_piece['rank']}. As the attacker is a higher rank than the destination, you won the battle. Here is the updated board state:\n"
                                f"{self._render_board(player_id=player_id, full_board=False)}"
                            ),
                            for_logging=False
                        )

                        self.state.add_observation(
                            from_id=-1,
                            to_id=1 - player_id,
                            message=(
                                f"Player {player_id} has moved a piece from {source} to {dest}. The attacking piece was {attacking_piece['rank']} and the destination piece was {target_piece['rank']}. As the attacker is a higher rank than the destination, you lost the battle. Here is the updated board state:\n"
                                f"{self._render_board(player_id=1 - player_id, full_board=False)}"
                            ),
                            for_logging=False
                        )

                    else:
                        ## defender wins
                        self.board[src_row][src_col] = None
                        self.player_pieces[player_id].remove((src_row, src_col))

                        ## add the observation to both players separately
                        self.state.add_observation(
                            from_id=-1,
                            to_id=player_id,
                            message=(
                                f"You have moved your piece from {source} to {dest}. The attacking piece was {attacking_piece['rank']} and the destination piece was {target_piece['rank']}. As the attacker is a lower rank than the destination, you lost the battle. Here is the updated board state:\n"
                                f"{self._render_board(player_id=player_id, full_board=False)}"
                            ),
                            for_logging=False
                        )

                        self.state.add_observation(
                            from_id=-1,
                            to_id=1 - player_id,
                            message=(
                                f"Player {player_id} has moved a piece from {source} to {dest}. The attacking piece was {attacking_piece['rank']} and the destination piece was {target_piece['rank']}. As the attacker is a lower rank than the destination, you won the battle. Here is the updated board state:\n"
                                f"{self._render_board(player_id=1 - player_id, full_board=False)}"
                            ),
                            for_logging=False
                        )


        ## update the rendered board
        self.state.game_state["rendered_board"] = self._render_board(player_id=player_id, full_board=True)

        return self.state.step()
    
    def render(
        self
    ):
        """
        Render the environment.
        """
        return self._render_board(player_id=self.state.current_player, full_board=True)

