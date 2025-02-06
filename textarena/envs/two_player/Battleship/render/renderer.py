from textarena.wrappers.RenderWrappers.PrettyRenderWrapper.base import BaseRenderer
import shutil
from pathlib import Path

class BattleshipRenderer(BaseRenderer):
    """Battleship-specific browser renderer"""
    
    def __init__(self, env, player_names=None, port=8000, host="127.0.0.1"):
        super().__init__(env, player_names, port, host)
        self._setup_ship_images()

    def _setup_ship_images(self):
        """Set up Battleship ship images"""
        ships_dir = self.static_dir / "ships"
        ships_dir.mkdir(exist_ok=True)
        
        # Copy ship images from assets
        assets_dir = Path(__file__).parent / "assets" / "ships"
        if assets_dir.exists():
            for ship in ['carrier', 'battleship', 'cruiser', 'submarine', 'destroyer', 'hit', 'miss']:
                src = assets_dir / f"{ship}.png"
                if src.exists():
                    shutil.copy(src, ships_dir / f"{ship}.png")

    def get_state(self) -> dict:
        """Get Battleship-specific state"""
        try:
            board = self.env.board
            return {
                "grid": board.grid if board else [['.' for _ in range(10)] for _ in range(10)],
                "current_player": "Player 1" if self.env.state.current_player_id == 0 else "Player 2",
                "hits": board.hits if board else [],
                "misses": board.misses if board else [],
                "ships_remaining": board.ships_remaining if board else 5,
                "game_over": board.game_over if board else False,
                "winner": board.winner if board else None,
                "ships": [
                    {"type": "carrier", "size": 5, "positions": [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]},
                    {"type": "battleship", "size": 4, "positions": [(1, 0), (1, 1), (1, 2), (1, 3)]},
                    {"type": "cruiser", "size": 3, "positions": [(2, 0), (2, 1), (2, 2)]},
                    {"type": "submarine", "size": 3, "positions": [(3, 0), (3, 1), (3, 2)]},
                    {"type": "destroyer", "size": 2, "positions": [(4, 0), (4, 1)]}
                ]
            }
        except Exception as e:
            print(f"Error getting state: {e}")
            return {
                "grid": [['.' for _ in range(10)] for _ in range(10)],
                "current_player": "Player 1",
                "hits": [],
                "misses": [],
                "ships_remaining": 5,
                "game_over": False,
                "winner": None,
                "ships": [
                    {"type": "carrier", "size": 5, "positions": [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]},
                    {"type": "battleship", "size": 4, "positions": [(1, 0), (1, 1), (1, 2), (1, 3)]},
                    {"type": "cruiser", "size": 3, "positions": [(2, 0), (2, 1), (2, 2)]},
                    {"type": "submarine", "size": 3, "positions": [(3, 0), (3, 1), (3, 2)]},
                    {"type": "destroyer", "size": 2, "positions": [(4, 0), (4, 1)]}
                ]
            }

    def get_custom_js(self) -> str:
        """Get Battleship-specific JavaScript code"""
        return """
        console.log('Loading Battleship components...');

        // Battleship components
        const BattleshipGrid = ({ grid, ships }) => {
            const renderCell = (row, col) => {
                const cell = grid[row][col];
                const isHit = cell === 'X';
                const isMiss = cell === '#';
                const isShip = ships.some(ship => 
                    ship.positions.some(pos => pos[0] === row && pos[1] === col)
                );
                
                let cellClass = 'cell';
                if (isHit) cellClass += ' hit';
                if (isMiss) cellClass += ' miss';
                if (isShip) cellClass += ' ship';

                return (
                    <div 
                        key={`${row}-${col}`} 
                        className={cellClass}
                        onClick={() => handleCellClick(row, col)}
                    >
                        {isHit && <img src="/static/ships/hit.png" alt="Hit" className="cell-img" />}
                        {isMiss && <img src="/static/ships/miss.png" alt="Miss" className="cell-img" />}
                        {isShip && <img src="/static/ships/ship.png" alt="Ship" className="cell-img" />}
                    </div>
                );
            };

            const handleCellClick = (row, col) => {
                console.log(`Cell clicked: ${row}, ${col}`);
                // Send the move to the server
                const ws = new WebSocket(`ws://${window.location.host}/ws`);
                ws.onopen = () => {
                    ws.send(JSON.stringify({ type: 'move', row, col }));
                    ws.close();
                };
            };

            return (
                <div className="grid-container">
                    <div className="battleship-grid">
                        {grid.map((row, rowIndex) => (
                            <div key={rowIndex} className="grid-row">
                                {row.map((_, colIndex) => renderCell(rowIndex, colIndex))}
                            </div>
                        ))}
                    </div>
                </div>
            );
        };

        const renderBattleshipGameInfo = (gameState) => {
            return (
                <div>
                    <div>Current Turn: {gameState.current_player}</div>
                    {gameState.game_over && <div className="alert">Game Over! {gameState.winner} wins!</div>}
                    <h3>Ships Remaining: {gameState.ships_remaining}</h3>
                    <h3>Hits: {gameState.hits.length}</h3>
                    <h3>Misses: {gameState.misses.length}</h3>
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
                            <BattleshipGrid grid={gameState.grid} ships={gameState.ships} />
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
            background: linear-gradient(45deg, #4CAF50, #2196F3);
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

        .grid-container {
            flex: 0 0 600px;
            background: #363636;
            padding: 20px;
            border-radius: 8px;
        }

        .battleship-grid {
            display: grid;
            grid-template-columns: repeat(10, 60px);
            grid-template-rows: repeat(10, 60px);
            width: 600px;
            height: 600px;
            border: 2px solid #404040;
        }

        .grid-row {
            display: flex;
        }

        .cell {
            width: 60px;
            height: 60px;
            display: flex;
            justify-content: center;
            align-items: center;
            border: 1px solid #404040;
            cursor: pointer;
        }

        .cell.hit { background-color: #ff4444; }
        .cell.miss { background-color: #2196F3; }
        .cell.ship { background-color: #769656; }

        .cell-img {
            width: 60px;
            height: 60px;
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

        .white-player { color: #ffffff; }
        .black-player { color: #000000; }

        .move-history {
            font-family: monospace;
            margin-top: 10px;
            background: #2B2B2B;
            padding: 12px;
            border-radius: 4px;
            max-height: 200px;
            overflow-y: auto;
        }

        .move {
            display: inline-block;
            margin: 2px 0;
            padding: 2px 6px;
            border-radius: 3px;
        }

        .move.white {
            color: #ffffff;
            background: #404040;
        }

        .move.black {
            color: #a0a0a0;
            background: #333333;
        }

        .move-number {
            color: #666666;
            margin-right: 4px;
        }

        .move-pair {
            display: block;
            margin-bottom: 4px;
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

        .chat-message.white .player-name { color: #ffffff; }
        .chat-message.black .player-name { color: #a0a0a0; }
        """
