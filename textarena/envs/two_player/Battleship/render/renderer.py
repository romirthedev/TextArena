from textarena.wrappers.RenderWrappers.PrettyRenderWrapper.base import BaseRenderer
import shutil
from pathlib import Path

class BattleshipRenderer(BaseRenderer):
    """Battleship-specific browser renderer"""
    
    def __init__(self, env, player_names=None, port=8000, host="127.0.0.1"):
        super().__init__(env, player_names, port, host)
        self._setup_ship_images()

    def _setup_ship_images(self):
        """Set up battleship images"""
        ships_dir = self.static_dir / "ships"
        ships_dir.mkdir(exist_ok=True)
        
        # Ship image sources - replace these URLs with actual image files
        ship_images = {
            'carrier': 'https://example.com/carrier.png',  # 5 spaces
            'battleship': 'https://example.com/battleship.png',  # 4 spaces
            'cruiser': 'https://example.com/cruiser.png',  # 3 spaces
            'submarine': 'https://example.com/submarine.png',  # 3 spaces
            'destroyer': 'https://example.com/destroyer.png',  # 2 spaces
            'hit': 'https://example.com/hit.png',
            'miss': 'https://example.com/miss.png'
        }
        
        # Copy ship images from assets
        assets_dir = Path(__file__).parent / "assets" / "ships"
        if assets_dir.exists():
            for ship_type in ship_images.keys():
                src = assets_dir / f"{ship_type}.png"
                if src.exists():
                    shutil.copy(src, ships_dir / f"{ship_type}.png")

    def get_state(self) -> dict:
        """Get battleship-specific state"""
        try:
            game = self.env.game
            return {
                "player_boards": {
                    "0": self._get_board_state(0),
                    "1": self._get_board_state(1)
                },
                "current_player": "Player 1" if self.env.state.current_player_id == 0 else "Player 2",
                "phase": self.env.state.phase,  # 'placement' or 'shooting'
                "last_shot": self.env.state.last_shot if hasattr(self.env.state, 'last_shot') else None,
                "game_over": self.env.state.game_over if hasattr(self.env.state, 'game_over') else False,
                "winner": self.env.state.winner if hasattr(self.env.state, 'winner') else None,
                "shot_history": self.env.state.shot_history if hasattr(self.env.state, 'shot_history') else []
            }
        except Exception as e:
            print(f"Error getting state: {e}")
            return {
                "player_boards": {
                    "0": self._get_empty_board(),
                    "1": self._get_empty_board()
                },
                "current_player": "Player 1",
                "phase": "placement",
                "last_shot": None,
                "game_over": False,
                "winner": None,
                "shot_history": []
            }

    def _get_board_state(self, player_id):
        """Get the state of a player's board"""
        try:
            return {
                "ships": self.env.game.get_ships(player_id),
                "hits": self.env.game.get_hits(player_id),
                "misses": self.env.game.get_misses(player_id)
            }
        except:
            return self._get_empty_board()

    def _get_empty_board(self):
        """Return an empty board state"""
        return {
            "ships": [],
            "hits": [],
            "misses": []
        }

    def get_custom_js(self) -> str:
        """Get battleship-specific JavaScript code"""
        return """
        console.log('Loading battleship components...');

        // Battleship components
        const BattleshipBoard = ({ board, isOpponent, phase }) => {
            const renderSquare = (i) => {
                const col = i % 10;
                const row = Math.floor(i / 10);
                const coordinate = `${String.fromCharCode(65 + col)}${row + 1}`;
                
                return (
                    <div key={i} className="square">
                        {getSquareContent(board, coordinate, isOpponent, phase)}
                    </div>
                );
            };

            return (
                <div className="board-container">
                    <div className="battleship-board">
                        {[...Array(100)].map((_, i) => renderSquare(i))}
                    </div>
                </div>
            );
        };

        const getSquareContent = (board, coordinate, isOpponent, phase) => {
            if (board.hits.includes(coordinate)) {
                return <img src="/static/ships/hit.png" alt="Hit" className="marker-img" />;
            }
            if (board.misses.includes(coordinate)) {
                return <img src="/static/ships/miss.png" alt="Miss" className="marker-img" />;
            }
            if (!isOpponent && board.ships.some(ship => ship.coordinates.includes(coordinate))) {
                const ship = board.ships.find(ship => ship.coordinates.includes(coordinate));
                return <img src={`/static/ships/${ship.type}.png`} alt={ship.type} className="ship-img" />;
            }
            return null;
        };

        const renderBattleshipGameInfo = (gameState) => {
            const shotHistoryRef = React.useRef(null);

            React.useEffect(() => {
                if (shotHistoryRef.current) {
                    shotHistoryRef.current.scrollTop = shotHistoryRef.current.scrollHeight;
                }
            }, [gameState.shot_history]);

            return (
                <div>
                    <div>Current Turn: {gameState.current_player}</div>
                    <div>Phase: {gameState.phase}</div>
                    {gameState.game_over && (
                        <div className="alert">Game Over! Winner: {gameState.winner}</div>
                    )}

                    <h3>Players</h3>
                    <div className="players">
                        {Object.entries(gameState.player_names).map(([id, name]) => (
                            <div key={id} className={`player-${id}`}>
                                {name} (Player {parseInt(id) + 1})
                            </div>
                        ))}
                    </div>

                    <h3>Shot History</h3>
                    <div 
                        className="shot-history"
                        ref={shotHistoryRef}
                    >
                        {gameState.shot_history.map((shot, i) => (
                            <div key={i} className="shot-entry">
                                <span className="shot-number">{i + 1}.</span>
                                <span className={`shot ${shot.player}`}>
                                    {shot.player}: {shot.coordinate} - {shot.result}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            );
        };

        // Main app
        const BattleshipGame = () => {
            console.log('Initializing BattleshipGame');
            const [gameState, setGameState] = React.useState(null);

            React.useEffect(() => {
                const ws = new WebSocket(`ws://${window.location.host}/ws`);
                ws.onopen = () => console.log('WebSocket connected');
                ws.onmessage = (event) => {
                    const state = JSON.parse(event.data);
                    console.log('Received state:', state);
                    setGameState(state);
                };
                return () => ws.close();
            }, []);

            if (!gameState) {
                console.log('Waiting for game state...');
                return <div>Loading game state...</div>;
            }

            return (
                <BaseGameContainer gameState={gameState} renderGameInfo={renderBattleshipGameInfo}>
                    <div className="battleship-layout">
                        <div className="main-content">
                            <div className="boards-container">
                                <div className="player-board">
                                    <h3>Your Board</h3>
                                    <BattleshipBoard 
                                        board={gameState.player_boards["0"]}
                                        isOpponent={false}
                                        phase={gameState.phase}
                                    />
                                </div>
                                <div className="opponent-board">
                                    <h3>Opponent's Board</h3>
                                    <BattleshipBoard 
                                        board={gameState.player_boards["1"]}
                                        isOpponent={true}
                                        phase={gameState.phase}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </BaseGameContainer>
            );
        };

        // Initialize the app
        console.log('Initializing React app');
        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<BattleshipGame />);
        console.log('Battleship components loaded');
        """

    def get_custom_css(self) -> str:
        return """
        .game-header {
            text-align: center;
            margin-bottom: 20px;
        }

        .game-title {
            font-size: 32px;
            font-weight: bold;
            color: #ffffff;
            margin: 0;
            padding: 10px 0;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            background: linear-gradient(45deg, #1E88E5, #00ACC1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
        }

        .main-content {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }

        .boards-container {
            display: flex;
            gap: 40px;
            justify-content: center;
        }

        .player-board, .opponent-board {
            flex: 0 0 400px;
            background: #363636;
            padding: 20px;
            border-radius: 8px;
        }

        .battleship-board {
            display: grid;
            grid-template-columns: repeat(10, 1fr);
            width: 400px;
            height: 400px;
            border: 2px solid #404040;
            background: #0077be;
        }

        .square {
            width: 40px;
            height: 40px;
            display: flex;
            justify-content: center;
            align-items: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
            position: relative;
        }

        .ship-img, .marker-img {
            width: 35px;
            height: 35px;
            user-select: none;
        }

        .info-container {
            flex: 1;
            background: #363636;
            padding: 20px;
            border-radius: 8px;
        }

        .status { margin-bottom: 20px; }
        .alert { color: #ff4444; font-weight: bold; }
        
        .players {
            margin-bottom: 20px;
        }

        .player-0 { color: #4CAF50; }
        .player-1 { color: #2196F3; }

        .shot-history {
            font-family: monospace;
            margin-top: 10px;
            background: #2B2B2B;
            padding: 12px;
            border-radius: 4px;
            max-height: 200px;
            overflow-y: auto;
        }

        .shot-entry {
            margin: 2px 0;
            padding: 2px 6px;
            border-radius: 3px;
        }

        .shot {
            display: inline-block;
            margin-left: 8px;
            padding: 2px 6px;
            border-radius: 3px;
        }

        .shot.Player1 {
            color: #4CAF50;
            background: #1b3a1b;
        }

        .shot.Player2 {
            color: #2196F3;
            background: #1a2c3d;
        }

        .shot-number {
            color: #666666;
        }

        .chat-message {
            margin-bottom: 10px;
            padding: 8px;
            border-radius: 4px;
            background: #404040;
        }

        .chat-message .player-name {
            font-weight: bold;
            margin-bottom: 5px;
        }

        .chat-message.player-1 .player-name { color: #4CAF50; }
        .chat-message.player-2 .player-name { color: #2196F3; }
        """
