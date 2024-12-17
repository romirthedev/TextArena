from textarena.wrappers.RenderWrappers.OfflineBrowserWrapper.base import BaseRenderer
import shutil
from pathlib import Path

class TakRenderer(BaseRenderer):
    """Tak-specific browser renderer"""

    def __init__(self, env, player_names=None, port=8000, host="127.0.0.1"):
        super().__init__(env, player_names, port, host)

    def get_state(self) -> dict:
        """Get Tak-specific state"""
        try:
            board = self.env.board
            return {
                "board": board or [],  # Assuming board is a nested list
                "current_player": self.env.state.current_player_id if self.env.state else "Unknown",
                "player_pieces": self.env.players or {},
            }
        except Exception as e:
            print(f"Error getting state: {e}")
            return {
                "board": [],
                "current_player": "Unknown",
                "player_pieces": {},
            }

    def get_custom_js(self) -> str:
        """Get Tak-specific JavaScript code"""
        return """
        console.log('Loading Tak components...');

        const TakBoard = ({ board }) => {
            return (
                <div className="board-container">
                    <table className="tak-board">
                        <tbody>
                            {board.map((row, rowIndex) => (
                                <tr key={rowIndex}>
                                    {row.map((cell, cellIndex) => (
                                        <td
                                            key={cellIndex}
                                            className={`cell ${((rowIndex + cellIndex) % 2 === 0) ? "light" : "dark"}`}
                                        >
                                            <div className="cell-content">
                                                {Array.isArray(cell) && cell.length > 0 ? (
                                                    <div className="cell-list">
                                                        {/* Render the items in the original order */}
                                                        {cell.map((item, itemIndex) => (
                                                            <span key={itemIndex} className="cell-item">
                                                                {item}
                                                            </span>
                                                        ))}
                                                    </div>
                                                ) : (
                                                    <span className="cell-item">
                                                        {cell !== null ? cell : ""}
                                                    </span>
                                                )}
                                            </div>
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            );
        };
        
        const renderTakGameInfo = (gameState) => {
            const currentPlayerName = gameState.player_names[gameState.current_player];

            return (
                <div>
                    <h3>Current Turn: {currentPlayerName}</h3>
                    <h3>Player Pieces</h3>
                    <div className="players">
                         {Object.entries(gameState.player_names).map(([id, name]) => (
                            <div key={id}>
                                {name} - 
                                Stones: {gameState.player_pieces[id]?.stones}, 
                                Capstones: {gameState.player_pieces[id]?.capstones}
                            </div>
                        ))}
                    </div>
                </div>
            );
        }


        const TakGame = () => {
            console.log('Initializing TakGame');
            const [gameState, setGameState] = React.useState(null);

            React.useEffect(() => {
                const ws = new WebSocket(`ws://${window.location.host}/ws`);
                ws.onopen = () => console.log('WebSocket connected');
                ws.onmessage = (event) => {
                    try {
                        const state = JSON.parse(event.data);
                        console.log('Received state:', state);
                        setGameState(state);
                    } catch (err) {
                        console.error('Error parsing WebSocket message:', err);
                    }
                };
                ws.onclose = () => console.log('WebSocket connection closed');
                return () => ws.close();
            }, []);

            if (!gameState) {
                console.log('Waiting for game state...');
                return <div>Loading game state...</div>;
            }

            return (
                <BaseGameContainer className="tak-layout" gameState={gameState} renderGameInfo={renderTakGameInfo}>
                    <div className="main-content">
                        <TakBoard board={gameState.board} />
                    </div>
                </BaseGameContainer>
            );
        };

        // Initialize the app
        console.log('Initializing React app');
        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<TakGame />);
        console.log('Tak components loaded');
        """

    def get_custom_css(self) -> str:
        """Get custom CSS styles for Tak game"""
        return """
        .main-content {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }

        /* Board container for dynamic, centered sizing */
        .board-container {
            flex: 0 0 600px;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: auto;
            overflow: hidden;
        }

        /* Main board table */
        .tak-board {
            border-collapse: collapse;
            width: 600px; /* Fill container */
            height: 600px; /* Ensure square grid */
            table-layout: fixed; /* Ensure fixed column width */
        }

        /* Individual cells */
        .tak-board td {
            border: 1px solid #555;
            position: relative;
            text-align: center;
            vertical-align: middle;
            background-color: #d7b899; /* Default light square */
        }

        .tak-board td.light {
            background-color: #d7b899; /* Light square */
        }

        .tak-board td.dark {
            background-color: #a97d55; /* Dark square */
        }

        /* Ensures cells remain square */
        .tak-board td::before {
            content: "";
            display: block;
            padding-top: 100%; /* Maintains aspect ratio */
        }

        /* Content inside cells */
        .cell-content {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 1.3rem;
            font-weight: bold;
            color: #333;
        }



        .players {
            margin-bottom: 20px;
        }
        """
