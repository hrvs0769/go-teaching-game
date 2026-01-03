const { useState, useEffect, useRef } = React;

// ========== 音效管理器 ==========
class SoundManager {
    constructor() {
        this.audioContext = null;
        this.enabled = true;
        this.initialized = false;
    }

    init() {
        if (this.initialized) return;
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.initialized = true;
        } catch (e) {
            this.enabled = false;
        }
    }

    playPlaceStone() {
        if (!this.enabled || !this.audioContext) return;
        const ctx = this.audioContext;
        const now = ctx.currentTime;

        const oscillator = ctx.createOscillator();
        const gainNode = ctx.createGain();
        const filter = ctx.createBiquadFilter();

        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(800, now);
        oscillator.frequency.exponentialRampToValueAtTime(200, now + 0.1);

        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(2000, now);

        gainNode.gain.setValueAtTime(0.3, now);
        gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.15);

        oscillator.connect(filter);
        filter.connect(gainNode);
        gainNode.connect(ctx.destination);

        oscillator.start(now);
        oscillator.stop(now + 0.15);
        this.playWoodNoise(now);
    }

    playWoodNoise(time) {
        if (!this.audioContext) return;
        const ctx = this.audioContext;
        const bufferSize = ctx.sampleRate * 0.05;
        const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const data = buffer.getChannelData(0);

        for (let i = 0; i < bufferSize; i++) {
            data[i] = (Math.random() * 2 - 1) * 0.5;
        }

        const noise = ctx.createBufferSource();
        const noiseGain = ctx.createGain();
        const noiseFilter = ctx.createBiquadFilter();

        noise.buffer = buffer;
        noiseFilter.type = 'highpass';
        noiseFilter.frequency.value = 1000;

        noiseGain.gain.setValueAtTime(0.15, time);
        noiseGain.gain.exponentialRampToValueAtTime(0.01, time + 0.05);

        noise.connect(noiseFilter);
        noiseFilter.connect(noiseGain);
        noiseGain.connect(ctx.destination);

        noise.start(time);
        noise.stop(time + 0.05);
    }

    playCapture() {
        if (!this.enabled || !this.audioContext) return;
        const ctx = this.audioContext;
        const now = ctx.currentTime;

        for (let i = 0; i < 3; i++) {
            const oscillator = ctx.createOscillator();
            const gainNode = ctx.createGain();

            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(1200 - i * 200, now + i * 0.08);

            gainNode.gain.setValueAtTime(0.25, now + i * 0.08);
            gainNode.gain.exponentialRampToValueAtTime(0.01, now + i * 0.08 + 0.1);

            oscillator.connect(gainNode);
            gainNode.connect(ctx.destination);

            oscillator.start(now + i * 0.08);
            oscillator.stop(now + i * 0.08 + 0.1);
        }
    }

    playPass() {
        if (!this.enabled || !this.audioContext) return;
        const ctx = this.audioContext;
        const now = ctx.currentTime;

        const oscillator = ctx.createOscillator();
        const gainNode = ctx.createGain();

        oscillator.type = 'triangle';
        oscillator.frequency.setValueAtTime(400, now);
        oscillator.frequency.setValueAtTime(600, now + 0.1);

        gainNode.gain.setValueAtTime(0.2, now);
        gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.2);

        oscillator.connect(gainNode);
        gainNode.connect(ctx.destination);

        oscillator.start(now);
        oscillator.stop(now + 0.2);
    }

    playGameOver() {
        if (!this.enabled || !this.audioContext) return;
        const ctx = this.audioContext;
        const now = ctx.currentTime;

        const notes = [523.25, 659.25, 783.99];
        notes.forEach((freq, i) => {
            const oscillator = ctx.createOscillator();
            const gainNode = ctx.createGain();

            oscillator.type = 'sine';
            oscillator.frequency.value = freq;

            gainNode.gain.setValueAtTime(0, now + i * 0.15);
            gainNode.gain.linearRampToValueAtTime(0.2, now + i * 0.15 + 0.05);
            gainNode.gain.exponentialRampToValueAtTime(0.01, now + i * 0.15 + 0.4);

            oscillator.connect(gainNode);
            gainNode.connect(ctx.destination);

            oscillator.start(now + i * 0.15);
            oscillator.stop(now + i * 0.15 + 0.4);
        });
    }

    playGameStart() {
        if (!this.enabled || !this.audioContext) return;
        const ctx = this.audioContext;
        const now = ctx.currentTime;

        const oscillator = ctx.createOscillator();
        const gainNode = ctx.createGain();

        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(400, now);
        oscillator.frequency.exponentialRampToValueAtTime(800, now + 0.3);

        gainNode.gain.setValueAtTime(0, now);
        gainNode.gain.linearRampToValueAtTime(0.15, now + 0.1);
        gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.4);

        oscillator.connect(gainNode);
        gainNode.connect(ctx.destination);

        oscillator.start(now);
        oscillator.stop(now + 0.4);
    }

    toggle() {
        this.enabled = !this.enabled;
        return this.enabled;
    }
}

const soundManager = new SoundManager();

// 围棋棋盘组件
function GoBoard({ board, size, onMove, validMoves, lastMove, disabled }) {
    const canvasRef = useRef(null);
    const [hoverPos, setHoverPos] = useState(null);

    const [dimensions, setDimensions] = useState(() => {
        const isMobile = window.innerWidth < 768;
        const containerWidth = Math.min(window.innerWidth - 40, 650);
        const cellSize = isMobile ? Math.floor((containerWidth - 50) / size) : 35;
        const margin = Math.floor(cellSize * 1.3);
        const boardSize = cellSize * (size - 1) + margin * 2;
        return { cellSize, margin, boardSize };
    });

    const { cellSize, margin, boardSize } = dimensions;

    useEffect(() => {
        const handleResize = () => {
            const isMobile = window.innerWidth < 768;
            const containerWidth = Math.min(window.innerWidth - 40, 650);
            const newCellSize = isMobile ? Math.floor((containerWidth - 50) / size) : 35;
            const newMargin = Math.floor(newCellSize * 1.3);
            const newBoardSize = newCellSize * (size - 1) + newMargin * 2;
            setDimensions({
                cellSize: newCellSize,
                margin: newMargin,
                boardSize: newBoardSize
            });
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [size]);

    useEffect(() => {
        if (!board || !canvasRef.current) return;
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        drawBoard(ctx);
    }, [board, hoverPos, lastMove, dimensions]);

    const drawBoard = (ctx) => {
        if (!board) return;

        ctx.clearRect(0, 0, boardSize, boardSize);

        // 木纹背景
        const gradient = ctx.createLinearGradient(0, 0, boardSize, boardSize);
        gradient.addColorStop(0, '#DEB887');
        gradient.addColorStop(0.5, '#D2A859');
        gradient.addColorStop(1, '#C9983C');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, boardSize, boardSize);

        ctx.strokeStyle = '#3E2723';
        ctx.lineWidth = Math.max(1.5, cellSize / 25);

        for (let i = 0; i < size; i++) {
            const pos = margin + i * cellSize;
            ctx.beginPath();
            ctx.moveTo(margin, pos);
            ctx.lineTo(boardSize - margin, pos);
            ctx.stroke();

            ctx.beginPath();
            ctx.moveTo(pos, margin);
            ctx.lineTo(pos, boardSize - margin);
            ctx.stroke();
        }

        // 星位
        const drawStarPoints = (points) => {
            ctx.fillStyle = '#3E2723';
            points.forEach(([sx, sy]) => {
                const px = margin + sx * cellSize;
                const py = margin + sy * cellSize;
                ctx.beginPath();
                ctx.arc(px, py, Math.max(3.5, cellSize / 8), 0, 2 * Math.PI);
                ctx.fill();
            });
        };

        if (size === 19) {
            drawStarPoints([[3, 3], [3, 9], [3, 15], [9, 3], [9, 9], [9, 15], [15, 3], [15, 9], [15, 15]]);
        } else if (size === 13) {
            drawStarPoints([[3, 3], [3, 9], [6, 6], [9, 3], [9, 9]]);
        } else if (size === 9) {
            drawStarPoints([[2, 2], [2, 6], [4, 4], [6, 2], [6, 6]]);
        }

        // 绘制坐标标记
        ctx.fillStyle = '#3E2723';
        ctx.font = `bold ${Math.max(10, cellSize * 0.35)}px Arial`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        // 生成字母序列（跳过I）
        const getLetter = (index) => {
            const letters = 'ABCDEFGHJKLMNOPQRST'; // 跳过I
            return letters[index] || '';
        };

        // 绘制顶部和底部数字（横向坐标）
        for (let i = 0; i < size; i++) {
            const num = i + 1;
            const pos = margin + i * cellSize;

            // 顶部数字
            ctx.fillText(num.toString(), pos, margin / 2);

            // 底部数字
            ctx.fillText(num.toString(), pos, boardSize - margin / 2);
        }

        // 绘制左侧和右侧字母（纵向坐标）
        for (let i = 0; i < size; i++) {
            const letter = getLetter(size - 1 - i); // 从上到下：T, S, R, ...
            const pos = margin + i * cellSize;

            // 左侧字母
            ctx.fillText(letter, margin / 2, pos);

            // 右侧字母
            ctx.fillText(letter, boardSize - margin / 2, pos);
        }

        // 绘制棋子
        for (let y = 0; y < size; y++) {
            for (let x = 0; x < size; x++) {
                if (board[y] && board[y][x] !== 0) {
                    const px = margin + x * cellSize;
                    const py = margin + y * cellSize;
                    drawStone(ctx, px, py, board[y][x]);
                }
            }
        }

        // 最后落子标记
        if (lastMove && board[lastMove.y] && board[lastMove.y][lastMove.x] !== undefined) {
            const px = margin + lastMove.x * cellSize;
            const py = margin + lastMove.y * cellSize;
            ctx.strokeStyle = board[lastMove.y][lastMove.x] === 1 ? '#fff' : '#000';
            ctx.lineWidth = Math.max(2, cellSize / 12);
            ctx.beginPath();
            ctx.arc(px, py, Math.max(4, cellSize / 7), 0, 2 * Math.PI);
            ctx.stroke();
        }

        // 悬停提示（仅桌面端）
        if (hoverPos && !disabled && window.innerWidth >= 768) {
            const { x, y } = hoverPos;
            const px = margin + x * cellSize;
            const py = margin + y * cellSize;
            ctx.fillStyle = 'rgba(0, 0, 0, 0.25)';
            ctx.beginPath();
            ctx.arc(px, py, cellSize / 2 - 2, 0, 2 * Math.PI);
            ctx.fill();
        }
    };

    const drawStone = (ctx, x, y, color) => {
        const radius = cellSize / 2 - 2;
        const gradient = ctx.createRadialGradient(
            x - radius / 3, y - radius / 3, 0,
            x, y, radius
        );

        if (color === 1) {
            gradient.addColorStop(0, '#666');
            gradient.addColorStop(0.5, '#333');
            gradient.addColorStop(1, '#000');
        } else {
            gradient.addColorStop(0, '#fff');
            gradient.addColorStop(0.7, '#f5f5f5');
            gradient.addColorStop(1, '#ddd');
        }

        ctx.shadowColor = 'rgba(0, 0, 0, 0.4)';
        ctx.shadowBlur = Math.max(3, cellSize / 10);
        ctx.shadowOffsetX = Math.max(1.5, cellSize / 20);
        ctx.shadowOffsetY = Math.max(1.5, cellSize / 20);

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, 2 * Math.PI);
        ctx.fill();

        ctx.shadowColor = 'transparent';
    };

    const handleMouseMove = (e) => {
        if (disabled || window.innerWidth < 768) return;

        const canvas = canvasRef.current;
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const x = Math.round((e.clientX - rect.left - margin / scaleX) / cellSize);
        const y = Math.round((e.clientY - rect.top - margin / scaleY) / cellSize);

        if (x >= 0 && x < size && y >= 0 && y < size) {
            setHoverPos({ x, y });
        } else {
            setHoverPos(null);
        }
    };

    const handleClick = (e) => {
        if (disabled) return;

        const canvas = canvasRef.current;
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const x = Math.round((e.clientX - rect.left - margin / scaleX) / (cellSize / scaleX));
        const y = Math.round((e.clientY - rect.top - margin / scaleY) / (cellSize / scaleY));

        if (x >= 0 && x < size && y >= 0 && y < size) {
            onMove(x, y);
        }
    };

    const handleTouchStart = (e) => {
        if (disabled) return;
        e.preventDefault();

        const touch = e.touches[0];
        const canvas = canvasRef.current;
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const x = Math.round((touch.clientX - rect.left - margin / scaleX) / (cellSize / scaleX));
        const y = Math.round((touch.clientY - rect.top - margin / scaleY) / (cellSize / scaleY));

        if (x >= 0 && x < size && y >= 0 && y < size) {
            onMove(x, y);
        }
    };

    return (
        <canvas
            ref={canvasRef}
            width={boardSize}
            height={boardSize}
            className="board"
            style={{
                maxWidth: '100%',
                height: 'auto',
                touchAction: 'none',
                borderRadius: '12px'
            }}
            onMouseMove={handleMouseMove}
            onMouseLeave={() => setHoverPos(null)}
            onClick={handleClick}
            onTouchStart={handleTouchStart}
        />
    );
}

// 设置面板
function SetupPanel({ onStart }) {
    const [difficulty, setDifficulty] = useState('medium');
    const [size, setSize] = useState(19);
    const [playerColor, setPlayerColor] = useState('black');

    const handleStart = () => {
        const aiColor = playerColor === 'black' ? 2 : 1;
        onStart(difficulty, size, aiColor);
    };

    return (
        <div className="container setup-panel">
            <div className="header">
                <h1 className="game-title">
                    <span className="title-icon"><i className="fas fa-chess-board"></i></span>
                    围棋教学游戏
                    <span className="title-icon"><i className="fas fa-chess-board"></i></span>
                </h1>
                <p className="subtitle">与AI对弈，学习围棋策略</p>
            </div>

            <div className="form-group">
                <label>
                    <span className="label-icon">⚡</span>
                    AI难度
                </label>
                <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                    <option value="easy">简单（适合初学者）</option>
                    <option value="medium">中等（有一定基础）</option>
                    <option value="hard">困难（高水准挑战）</option>
                </select>
            </div>

            <div className="form-group">
                <label>
                    <span className="label-icon">📐</span>
                    棋盘大小
                </label>
                <select value={size} onChange={(e) => setSize(parseInt(e.target.value))}>
                    <option value={19}>19×19（标准）</option>
                    <option value={13}>13×13（快速）</option>
                    <option value={9}>9×9（入门）</option>
                </select>
            </div>

            <div className="form-group">
                <label>
                    <span className="label-icon">🎯</span>
                    执子颜色
                </label>
                <select value={playerColor} onChange={(e) => setPlayerColor(e.target.value)}>
                    <option value="black">黑棋（先手）</option>
                    <option value="white">白棋（后手）</option>
                </select>
            </div>

            <button className="btn btn-primary" onClick={handleStart}>
                <i className="fas fa-gamepad"></i> 开始游戏
            </button>
        </div>
    );
}

// 局势分析面板
function AnalysisPanel({ analysis, onClose }) {
    if (!analysis) return null;

    return (
        <div className="analysis-modal-overlay" onClick={onClose}>
            <div className="analysis-modal" onClick={(e) => e.stopPropagation()}>
                <div className="analysis-header">
                    <h2><i className="fas fa-chart-line"></i> 局势分析</h2>
                    <button className="close-btn" onClick={onClose}><i className="fas fa-times"></i></button>
                </div>

                <div className="analysis-content">
                    {/* 总体评估 */}
                    <div className="analysis-section">
                        <h3>🎯 总体评估</h3>
                        <div className="overall-assessment">
                            <div className="assessment-emoji">{analysis.overall_assessment.emoji}</div>
                            <div className="assessment-text">{analysis.overall_assessment.winner}</div>
                            <div className="assessment-score">
                                <span className="score-label">黑: {analysis.overall_assessment.black_score}</span>
                                <span className="score-divider">|</span>
                                <span className="score-label">白: {analysis.overall_assessment.white_score}</span>
                            </div>
                        </div>
                    </div>

                    {/* 领地分析 */}
                    <div className="analysis-section">
                        <h3><i className="fas fa-map"></i> 领地分析</h3>
                        <div className="territory-grid">
                            <div className="territory-item black">
                                <div className="territory-label">黑方</div>
                                <div className="territory-value">{analysis.territory.black}目</div>
                            </div>
                            <div className="territory-item neutral">
                                <div className="territory-label">中立</div>
                                <div className="territory-value">{analysis.territory.neutral}目</div>
                            </div>
                            <div className="territory-item white">
                                <div className="territory-label">白方</div>
                                <div className="territory-value">{analysis.territory.white}目</div>
                            </div>
                        </div>
                    </div>

                    {/* 双方实力 */}
                    <div className="analysis-section">
                        <h3><i className="fas fa-handshake"></i> 双方实力</h3>
                        <div className="strength-comparison">
                            <div className="strength-side">
                                <div className="strength-title"><i className="fas fa-circle" style={{color: '#000', fontSize: '0.8em'}}></i> 黑方</div>
                                <div className="strength-stats">
                                    <div className="stat-item">
                                        <span className="stat-label">棋子数</span>
                                        <span className="stat-value">{analysis.black_strength.stones}</span>
                                    </div>
                                    <div className="stat-item">
                                        <span className="stat-label">棋组数</span>
                                        <span className="stat-value">{analysis.black_strength.groups}</span>
                                    </div>
                                    <div className="stat-item">
                                        <span className="stat-label">提子数</span>
                                        <span className="stat-value">{analysis.black_strength.captured}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="strength-divider">VS</div>

                            <div className="strength-side">
                                <div className="strength-title"><i className="far fa-circle" style={{color: '#999', fontSize: '0.8em'}}></i> 白方</div>
                                <div className="strength-stats">
                                    <div className="stat-item">
                                        <span className="stat-label">棋子数</span>
                                        <span className="stat-value">{analysis.white_strength.stones}</span>
                                    </div>
                                    <div className="stat-item">
                                        <span className="stat-label">棋组数</span>
                                        <span className="stat-value">{analysis.white_strength.groups}</span>
                                    </div>
                                    <div className="stat-item">
                                        <span className="stat-label">提子数</span>
                                        <span className="stat-value">{analysis.white_strength.captured}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* 战略建议 */}
                    <div className="analysis-section">
                        <h3>💡 战略建议</h3>
                        <div className="recommendations">
                            {analysis.recommendations.map((rec, i) => (
                                <div key={i} className="recommendation-item">
                                    <span className="rec-bullet">•</span>
                                    <span>{rec}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* 游戏阶段 */}
                    <div className="analysis-section">
                        <div className="game-phase-info">
                            <span className="phase-icon">
                                {analysis.game_phase === 'opening' ? <i className="fas fa-sun"></i> :
                                 analysis.game_phase === 'middlegame' ? <i className="fas fa-fire"></i> : <i className="fas fa-flag-checkered"></i>}
                            </span>
                            <span className="phase-text">
                                {analysis.game_phase === 'opening' ? '开局阶段' :
                                 analysis.game_phase === 'middlegame' ? '中盘阶段' : '官子阶段'}
                            </span>
                            <span className="phase-moves">（第{analysis.move_count}手）</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// 落子日志面板
function LogsPanel({ logs, onClose }) {
    if (!logs) return null;

    return (
        <div className="logs-modal-overlay" onClick={onClose}>
            <div className="logs-modal" onClick={(e) => e.stopPropagation()}>
                <div className="logs-header">
                    <h2><i className="fas fa-scroll"></i> 落子日志</h2>
                    <button className="close-btn" onClick={onClose}><i className="fas fa-times"></i></button>
                </div>

                <div className="logs-content">
                    <div className="logs-list">
                        {logs.map((log, index) => (
                            <div key={index} className={`log-entry ${log.player_color === 1 ? 'black-move' : 'white-move'}`}>
                                <div className="log-number">
                                    <span className="log-num">{log.number}</span>
                                </div>
                                <div className="log-details">
                                    <div className="log-player">{log.player}</div>
                                    <div className="log-action">{log.action}</div>
                                    {log.position && <div className="log-position">{log.position}</div>}
                                    {log.captured > 0 && (
                                        <div className="log-captured">提{log.captured}子</div>
                                    )}
                                </div>
                            </div>
                        ))}
                        {logs.length === 0 && (
                            <div className="no-logs">暂无落子记录</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

// 游戏面板
function GamePanel({ game, onNewGame }) {
    const [error, setError] = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [soundEnabled, setSoundEnabled] = useState(true);
    const [analysis, setAnalysis] = useState(null);
    const [analyzing, setAnalyzing] = useState(false);
    const [logs, setLogs] = useState(null);
    const [showLogs, setShowLogs] = useState(false);

    useEffect(() => {
        soundManager.init();
        soundManager.playGameStart();
    }, []);

    const handleMove = async (x, y) => {
        if (isProcessing) return;

        setIsProcessing(true);
        setError(null);

        try {
            // 玩家落子 - 立即返回
            const response = await fetch(`/api/game/${game.id}/move`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ x, y })
            });

            const result = await response.json();

            if (result.error) {
                setError(result.error);
                soundManager.playPass();
                setIsProcessing(false);
                return;
            }

            soundManager.playPlaceStone();

            const oldCaptured = game.currentPlayer === 1 ? game.capturedWhite : game.capturedBlack;
            const newCaptured = result.current_player === 1 ? result.captured_white : result.captured_black;

            // 立即更新UI显示玩家落子
            game.updateState(result);

            if (newCaptured > oldCaptured) {
                setTimeout(() => soundManager.playCapture(), 100);
            }

            if (result.game_over) {
                game.setGameOver(true);
                setTimeout(() => soundManager.playGameOver(), 300);
                setIsProcessing(false);
                return;
            }

            // 如果接下来是AI回合，异步调用AI落子
            if (result.is_ai_turn) {
                // 延迟一下让玩家看到自己的落子
                setTimeout(async () => {
                    let retryCount = 0;
                    const maxRetries = 2;
                    let aiResult = null;

                    const tryAIMove = async () => {
                        try {
                            const aiResponse = await fetch(`/api/game/${game.id}/ai-move`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' }
                            });

                            aiResult = await aiResponse.json();

                            if (aiResult.error) {
                                // 如果是重试次数还没用完，自动重试
                                if (retryCount < maxRetries) {
                                    retryCount++;
                                    console.log(`AI落子失败，正在重试 (${retryCount}/${maxRetries})...`);
                                    setTimeout(tryAIMove, 500); // 500ms后重试
                                    return;
                                } else {
                                    setError(aiResult.error + ' 请刷新页面重新开始');
                                    setIsProcessing(false);
                                }
                            } else {
                                if (aiResult.ai_move) {
                                    soundManager.playPlaceStone();
                                }

                                const aiOldCaptured = game.currentPlayer === 1 ? game.capturedWhite : game.capturedBlack;
                                const aiNewCaptured = aiResult.current_player === 1 ? aiResult.captured_white : aiResult.captured_black;

                                game.updateState(aiResult);

                                if (aiNewCaptured > aiOldCaptured) {
                                    setTimeout(() => soundManager.playCapture(), 100);
                                }

                                if (aiResult.game_over) {
                                    game.setGameOver(true);
                                    setTimeout(() => soundManager.playGameOver(), 300);
                                }

                                setIsProcessing(false);
                            }
                        } catch (err) {
                            // 网络错误，也尝试重试
                            if (retryCount < maxRetries) {
                                retryCount++;
                                console.log(`网络错误，正在重试 (${retryCount}/${maxRetries})...`);
                                setTimeout(tryAIMove, 500);
                                return;
                            } else {
                                // 最后一次重试也失败
                                console.error('AI落子失败:', err);

                                // 关键修复：强制更新游戏状态，让轮次回到玩家
                                // 这样玩家可以继续落子
                                const currentState = {
                                    board: game.board,
                                    current_player: game.aiColor === 1 ? 2 : 1, // 切换到玩家
                                    captured_black: game.capturedBlack,
                                    captured_white: game.capturedWhite,
                                    last_move: game.lastMove
                                };

                                game.updateState(currentState);
                                setError('AI暂时无法响应，已切换到你继续落子');
                                setIsProcessing(false); // 重置状态
                            }
                        }
                    };

                    await tryAIMove();
                }, 300); // 300ms延迟让玩家看到自己的落子
            } else {
                setIsProcessing(false);
            }
        } catch (err) {
            console.error('玩家落子失败:', err);
            // 网络错误时，也要确保玩家能继续落子
            // 不改变轮次，因为落子可能没有成功
            setError('网络错误，请重试');
            setIsProcessing(false);
        }
    };

    const handlePass = async () => {
        if (isProcessing) return;

        setIsProcessing(true);
        setError(null);

        try {
            const response = await fetch(`/api/game/${game.id}/pass`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.error) {
                setError(result.error);
            } else {
                soundManager.playPass();
                game.updateState(result);

                if (result.game_over) {
                    game.setGameOver(true);
                    setTimeout(() => soundManager.playGameOver(), 300);
                }
            }
        } catch (err) {
            setError('网络错误，请重试');
        } finally {
            setIsProcessing(false);
        }
    };

    const handleAnalyze = async () => {
        setAnalyzing(true);
        try {
            const response = await fetch(`/api/game/${game.id}/analyze`, {
                method: 'POST'
            });

            const result = await response.json();
            setAnalysis(result);
        } catch (err) {
            setError('分析失败，请重试');
        } finally {
            setAnalyzing(false);
        }
    };

    const handleShowLogs = async () => {
        if (logs) {
            setShowLogs(true);
            return;
        }

        try {
            const response = await fetch(`/api/game/${game.id}/logs`);
            const result = await response.json();
            setLogs(result.logs);
            setShowLogs(true);
        } catch (err) {
            setError('获取日志失败，请重试');
        }
    };

    const toggleSound = () => {
        const enabled = soundManager.toggle();
        setSoundEnabled(enabled);
    };

    const getPlayerName = (player) => player === 1 ? '黑方' : '白方';

    return (
        <div className="container game-container">
            <div className="header">
                <h1 className="game-title-small">围棋教学</h1>
                <div className="header-buttons">
                    <button className="icon-btn" onClick={handleShowLogs} title="查看日志">
                        <i className="fas fa-scroll"></i>
                    </button>
                    <button
                        className={`icon-btn ${soundEnabled ? 'active' : ''}`}
                        onClick={toggleSound}
                        title={soundEnabled ? '关闭音效' : '开启音效'}
                    >
                        {soundEnabled ? <i className="fas fa-volume-up"></i> : <i className="fas fa-volume-mute"></i>}
                    </button>
                    <button className="icon-btn" onClick={onNewGame} title="新游戏">
                        <i className="fas fa-redo"></i>
                    </button>
                </div>
            </div>

            {error && (
                <div className="error-message">
                    <i className="fas fa-exclamation-triangle" style={{fontSize: '1.3em'}}></i>
                    {error}
                </div>
            )}

            <div className="game-area">
                <div className="board-section">
                    <GoBoard
                        board={game.board}
                        size={game.size}
                        onMove={handleMove}
                        lastMove={game.lastMove}
                        disabled={isProcessing || game.currentPlayer === game.aiColor}
                    />
                    <button
                        className="analyze-btn"
                        onClick={handleAnalyze}
                        disabled={analyzing || game.gameOver}
                    >
                        {analyzing ? '分析中...' : <><i className="fas fa-chart-line"></i> 分析局势</>}
                    </button>
                </div>

                <div className="info-panel">
                    <div className="panel-section">
                        <h3>游戏信息</h3>
                        <div className="status-info">
                            <div className="status-item">
                                <div className="status-label">当前轮次</div>
                                <div className="status-value">{getPlayerName(game.currentPlayer)}</div>
                            </div>
                            <div className="status-item">
                                <div className="status-label">AI执子</div>
                                <div className="status-value">{getPlayerName(game.aiColor)}</div>
                            </div>
                        </div>
                    </div>

                    <div className="panel-section">
                        <h3>提子统计</h3>
                        <div className="status-info">
                            <div className="status-item black-item">
                                <div className="status-label"><i className="fas fa-circle" style={{color: '#000', fontSize: '0.7em'}}></i> 黑方</div>
                                <div className="status-value">{game.capturedBlack}</div>
                            </div>
                            <div className="status-item white-item">
                                <div className="status-label"><i className="far fa-circle" style={{color: '#999', fontSize: '0.7em'}}></i> 白方</div>
                                <div className="status-value">{game.capturedWhite}</div>
                            </div>
                        </div>
                    </div>

                    {game.aiExplanation && (
                        <div className="panel-section">
                            <h3>AI思考</h3>
                            <div className="ai-explanation">
                                <div className="avatar">🤖</div>
                                <div className="text">{game.aiExplanation}</div>
                            </div>
                        </div>
                    )}

                    <div className="panel-section">
                        <button
                            className="btn btn-secondary"
                            onClick={handlePass}
                            disabled={isProcessing}
                            style={{ width: '100%' }}
                        >
                            虚着
                        </button>
                    </div>
                </div>
            </div>

            {game.gameOver && (
                <div className="game-over-modal">
                    <div className="modal-content">
                        <h2><i className="fas fa-trophy" style={{color: '#f59e0b'}}></i> 游戏结束</h2>
                        <div className="score">
                            <div className="score-row">
                                <span className="score-player"><i className="fas fa-circle" style={{color: '#000', fontSize: '0.8em'}}></i> 黑方</span>
                                <span className="score-points">{game.score?.black.toFixed(1)}分</span>
                            </div>
                            <div className="score-row">
                                <span className="score-player"><i className="far fa-circle" style={{color: '#999', fontSize: '0.8em'}}></i> 白方</span>
                                <span className="score-points">{game.score?.white.toFixed(1)}分</span>
                            </div>
                        </div>
                        <h3 className="winner-announcement">
                            {game.winner === 'black' ? <><i className="fas fa-circle" style={{color: '#000'}}></i> 黑方获胜！</> : <><i className="far fa-circle" style={{color: '#999'}}></i> 白方获胜！</>}
                        </h3>
                        <div className="modal-buttons">
                            <button className="btn btn-primary" onClick={onNewGame}>
                                <i className="fas fa-redo"></i> 再来一局
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {analysis && (
                <AnalysisPanel
                    analysis={analysis}
                    onClose={() => setAnalysis(null)}
                />
            )}

            {showLogs && logs && (
                <LogsPanel
                    logs={logs}
                    onClose={() => setShowLogs(false)}
                />
            )}
        </div>
    );
}

// 主应用
function App() {
    const [gameStarted, setGameStarted] = useState(false);
    const [gameState, setGameState] = useState(null);

    const startGame = async (difficulty, size, aiColor) => {
        try {
            const response = await fetch('/api/game/new', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ difficulty, size, aiColor })
            });

            const result = await response.json();

            if (result.success) {
                setGameState({
                    id: result.game.game_id,
                    size: result.game.board_size,
                    board: Array(size).fill(null).map(() => Array(size).fill(0)),
                    currentPlayer: result.game.current_player,
                    aiColor: result.game.ai_color,
                    capturedBlack: 0,
                    capturedWhite: 0,
                    lastMove: null,
                    aiExplanation: null,
                    gameOver: false,
                    score: null,
                    winner: null,

                    updateState(result) {
                        if (result.board) {
                            this.board = result.board;
                        }
                        this.currentPlayer = result.current_player;
                        this.capturedBlack = result.captured_black || 0;
                        this.capturedWhite = result.captured_white || 0;
                        this.lastMove = result.last_move || null;
                        this.aiExplanation = result.ai_explanation || null;
                        if (result.score) {
                            this.score = result.score;
                        }
                        if (result.winner) {
                            this.winner = result.winner;
                        }
                    }
                });

                setGameStarted(true);
            }
        } catch (err) {
            console.error('Failed to start game:', err);
        }
    };

    return (
        <div>
            {!gameStarted ? (
                <SetupPanel onStart={startGame} />
            ) : (
                <GamePanel
                    game={gameState}
                    onNewGame={() => {
                        setGameStarted(false);
                        setGameState(null);
                    }}
                />
            )}
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById('root'));
