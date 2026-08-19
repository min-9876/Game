const tg = window.Telegram.WebApp;
tg.expand();

const user = tg.initDataUnsafe.user;
document.getElementById('player-greeting').innerText = user ? `Player: ${user.first_name}` : "Player: Guest";

const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

let snake = [{x: 160, y: 160}, {x: 150, y: 160}];
let food = {x: 100, y: 100};
let dx = 10;
let dy = 0;
let score = 0;
let gameInterval = null;

function drawGame() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    ctx.fillStyle = '#f43f5e';
    ctx.fillRect(food.x, food.y, 10, 10);
    
    ctx.fillStyle = '#22c55e';
    snake.forEach(part => {
        ctx.fillRect(part.x, part.y, 10, 10);
    });
}

function moveSnake() {
    const head = {x: snake[0].x + dx, y: snake[0].y + dy};
    snake.unshift(head);
    
    if (head.x === food.x && head.y === food.y) {
        score += 10;
        document.getElementById('score').innerText = score;
        generateFood();
    } else {
        snake.pop();
    }
    
    if (head.x < 0 || head.x >= canvas.width || head.y < 0 || head.y >= canvas.height) {
        gameOver();
    }
}

function generateFood() {
    food.x = Math.floor(Math.random() * 32) * 10;
    food.y = Math.floor(Math.random() * 32) * 10;
}

function main() {
    moveSnake();
    drawGame();
}

function startGame() {
    snake = [{x: 160, y: 160}, {x: 150, y: 160}];
    dx = 10;
    dy = 0;
    score = 0;
    document.getElementById('score').innerText = score;
    generateFood();
    if(gameInterval) clearInterval(gameInterval);
    gameInterval = setInterval(main, 100);
}

function gameOver() {
    clearInterval(gameInterval);
    alert(`Game Over! Your Score: ${score}`);
    submitScore(score);
}

function submitScore(finalScore) {
    if (!user) return;
    fetch('/api/save_score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: user.id,
            first_name: user.first_name || "Player",
            score: finalScore
        })
    }).then(() => loadLeaderboard());
}

async function loadLeaderboard() {
    try {
        let res = await fetch('/api/leaderboard');
        let data = await res.json();
        if(data.status === 'success') {
            let html = '<ol>';
            data.top_players.forEach(p => {
                html += `<li>${p.first_name}: <b>${p.score}</b></li>`;
            });
            html += '</ol>';
            document.getElementById('leaderboard-list').innerHTML = html;
        }
    } catch(e) {
        console.error(e);
    }
}

window.addEventListener('keydown', e => {
    if(e.key === 'ArrowUp' && dy === 0) { dx = 0; dy = -10; }
    if(e.key === 'ArrowDown' && dy === 0) { dx = 0; dy = 10; }
    if(e.key === 'ArrowLeft' && dx === 0) { dx = -10; dy = 0; }
    if(e.key === 'ArrowRight' && dx === 0) { dx = 10; dy = 0; }
});

loadLeaderboard();
