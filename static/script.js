let state = {
    start: null,
    target: null,
    current: null,
    path: [],
    hops: 0,
    startTime: null,
    timerInterval: null
};

let debounceTimer;

document.addEventListener('DOMContentLoaded', () => {
    setupAutocomplete('start');
    setupAutocomplete('target');
    
    document.getElementById('random-btn').addEventListener('click', loadRandomVideos);
    document.getElementById('start-game-btn').addEventListener('click', startGame);
});

// Autocomplete and selection logic...
function setupAutocomplete(type) {
    const input = document.getElementById(`${type}-input`);
    const suggestions = document.getElementById(`${type}-suggestions`);

    input.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        const query = e.target.value;
        
        if (query.trim().length < 1) {
            suggestions.style.display = 'none';
            return;
        }
        
        suggestions.innerHTML = '<div style="padding: 1rem; text-align: center; color: var(--text-muted);">Buscando...</div>';
        suggestions.style.display = 'block';

        debounceTimer = setTimeout(() => fetchSuggestions(query.trim(), type), 250);
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.autocomplete-container')) {
            suggestions.style.display = 'none';
        }
    });
}

async function fetchSuggestions(query, type) {
    try {
        const response = await fetch(`/api/autocomplete?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        renderSuggestions(data, type);
    } catch (error) {
        console.error('Error fetching suggestions:', error);
    }
}

function renderSuggestions(data, type) {
    const suggestionsContainer = document.getElementById(`${type}-suggestions`);
    suggestionsContainer.innerHTML = '';

    if (data.length === 0) {
        suggestionsContainer.style.display = 'none';
        return;
    }

    data.forEach(video => {
        const item = document.createElement('div');
        item.className = 'suggestion-item';
        item.innerHTML = `
            <img src="${video.thumb}" alt="thumb" class="suggestion-thumb">
            <div class="suggestion-info">
                <div class="suggestion-title">${video.title}</div>
                <div class="suggestion-channel">${video.channel}${video.date ? ' · ' + video.date : ''}</div>
            </div>
        `;
        item.addEventListener('click', () => selectVideo(video, type));
        suggestionsContainer.appendChild(item);
    });

    suggestionsContainer.style.display = 'block';
}

function selectVideo(video, type) {
    state[type] = video;
    
    document.getElementById(`${type}-input`).style.display = 'none';
    document.getElementById(`${type}-suggestions`).style.display = 'none';
    
    const selectedEl = document.getElementById(`${type}-selected`);
    selectedEl.querySelector('.selected-thumb').src = video.thumb;
    selectedEl.querySelector('.selected-title').textContent = video.title;
    selectedEl.querySelector('.selected-channel').textContent = video.channel;
    selectedEl.style.display = 'flex';

    checkReady();
}

window.clearSelection = function(type) {
    state[type] = null;
    
    const input = document.getElementById(`${type}-input`);
    input.value = '';
    input.style.display = 'block';
    input.focus();
    
    document.getElementById(`${type}-selected`).style.display = 'none';
    
    checkReady();
}

async function loadRandomVideos() {
    const btn = document.getElementById('random-btn');
    btn.textContent = '⏳ Cargando...';
    btn.disabled = true;
    try {
        const response = await fetch('/api/random');
        const data = await response.json();

        if (!data.start || !data.target) {
            console.warn('Random API returned null, retrying...');
            btn.textContent = '🎲 Aleatorio';
            btn.disabled = false;
            alert('No se pudo obtener un video aleatorio. Intenta de nuevo.');
            return;
        }

        selectVideo(data.start, 'start');
        selectVideo(data.target, 'target');
    } catch (error) {
        console.error('Error loading random videos:', error);
        alert('Error al cargar videos aleatorios. Intenta de nuevo.');
    } finally {
        btn.textContent = '🎲 Aleatorio';
        btn.disabled = false;
    }
}

function checkReady() {
    const btn = document.getElementById('start-game-btn');
    btn.disabled = !(state.start && state.target);
}

// ==================== GAME LOGIC ====================

function updateTimer() {
    if (!state.startTime) return;
    const now = Date.now();
    const diffSeconds = Math.floor((now - state.startTime) / 1000);
    const mins = Math.floor(diffSeconds / 60).toString().padStart(2, '0');
    const secs = (diffSeconds % 60).toString().padStart(2, '0');
    document.getElementById('time-counter').textContent = `${mins}:${secs}`;
}

function startGame() {
    if (!state.start || !state.target) return;

    state.current = state.start;
    state.path = [state.start];
    state.hops = 0;
    
    // Start Timer
    state.startTime = Date.now();
    document.getElementById('time-counter').textContent = "00:00";
    if (state.timerInterval) clearInterval(state.timerInterval);
    state.timerInterval = setInterval(updateTimer, 1000);

    document.getElementById('setup-screen').style.display = 'none';
    document.getElementById('main-header').style.display = 'none';
    
    // Set fixed text for give up button
    document.getElementById('give-up-btn').textContent = "🏳️ Ya no puedo mas";
    
    document.getElementById('game-screen').style.display = 'block';

    document.getElementById('game-target-thumb').src = state.target.thumb;
    document.getElementById('game-target-title').textContent = state.target.title;
    document.getElementById('game-target-channel').textContent = state.target.channel;

    updateGameUI();
}

function updateGameUI() {
    if (state.current.id === state.target.id) {
        showWinScreen();
        return;
    }

    document.getElementById('youtube-player').src = `https://www.youtube.com/embed/${state.current.id}?autoplay=1`;
    document.getElementById('current-video-title').textContent = state.current.title;
    document.getElementById('current-video-channel').textContent = state.current.channel;
    document.getElementById('hop-counter').textContent = state.hops;

    renderPath('path-visualizer');
    loadRecommendations(state.current);
}

async function loadRecommendations(video) {
    const list = document.getElementById('recommendations-list');
    const loader = document.getElementById('loading-recs');
    
    list.innerHTML = '';
    loader.style.display = 'block';

    try {
        // Enviar IDs ya visitados para que el backend los filtre
        const visitedIds = state.path.map(v => v.id);
        
        const response = await fetch(`/api/recommendations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id: video.id,
                title: video.title,
                channel: video.channel,
                visited_ids: visitedIds
            })
        });
        const data = await response.json();
        
        loader.style.display = 'none';
        
        const recs = data.recommendations;
        
        if (recs.length === 0) {
            list.innerHTML = '<p style="color:var(--text-muted); padding: 1rem; text-align:center;">No hay más recomendaciones disponibles. Intenta rendirte o recargar.</p>';
            return;
        }
        
        recs.forEach((video, index) => {
            const card = document.createElement('div');
            card.className = 'video-card';
            card.innerHTML = `
                <img src="${video.thumb}" alt="thumb" class="video-thumb">
                <div class="video-info">
                    <div class="video-title" title="${video.title}">${video.title}</div>
                    <div class="video-channel">${video.channel}</div>
                </div>
            `;
            card.style.animation = `fadeIn 0.4s ease-out ${index * 0.04}s both`;
            card.addEventListener('click', () => jumpToVideo(video));
            list.appendChild(card);
        });

    } catch (error) {
        loader.style.display = 'none';
        list.innerHTML = '<p style="color:var(--accent-red); text-align:center;">Error al cargar recomendaciones.</p>';
        console.error(error);
    }
}

function jumpToVideo(video) {
    state.hops++;
    state.current = video;
    state.path.push(video);
    
    // Trigger glitch effect on video jump
    triggerGlitch();
    
    updateGameUI();
    document.getElementById('game-screen').scrollIntoView({ behavior: 'smooth' });
}

function renderPath(containerId) {
    const visualizer = document.getElementById(containerId);
    visualizer.innerHTML = '';
    
    state.path.forEach((video, index) => {
        const card = document.createElement('div');
        card.className = 'mini-card';
        card.innerHTML = `
            <img src="${video.thumb}" alt="thumb">
            <div class="title" title="${video.title}">${video.title}</div>
        `;
        visualizer.appendChild(card);

        if (index < state.path.length - 1) {
            const arrow = document.createElement('div');
            arrow.className = 'path-arrow';
            arrow.innerHTML = '➜';
            visualizer.appendChild(arrow);
        }
    });

    visualizer.scrollLeft = visualizer.scrollWidth;
}

// ==================== AUDIO & EFFECTS ====================
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

function playTone(freq, type, duration, startTime) {
    const osc = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    
    osc.type = type;
    osc.frequency.setValueAtTime(freq, startTime);
    
    gainNode.gain.setValueAtTime(0.1, startTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + duration);
    
    osc.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    
    osc.start(startTime);
    osc.stop(startTime + duration);
}

function playWinSound() {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const now = audioCtx.currentTime;
    // Arpegio ascendente feliz (8-bit style)
    [523.25, 659.25, 783.99, 1046.50].forEach((freq, i) => {
        playTone(freq, 'square', 0.15, now + i * 0.15);
    });
}

function playLoseSound() {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const now = audioCtx.currentTime;
    // Tonos descendentes tristes
    [300, 250, 200, 150].forEach((freq, i) => {
        playTone(freq, 'sawtooth', 0.2, now + i * 0.2);
    });
}

function triggerGlitch() {
    const overlay = document.getElementById('glitch-overlay');
    if (overlay) {
        overlay.classList.remove('active');
        void overlay.offsetWidth; // trigger reflow
        overlay.classList.add('active');
    }
}

// ==================== RANDOM TEXTS ====================
const surrenderTitles = [
    "Te perdiste en el abismo de YouTube",
    "El algoritmo te ha devorado",
    "Caíste en la espiral de videos recomendados",
    "Game Over: Tu cerebro se fundió"
];

const surrenderSubtitles = [
    "Tus saltos no tienen sentido, ni YouTube sabe cómo llegaste aquí.",
    "Ni con un mapa llegabas al objetivo.",
    "Demasiados videos de gatitos, perdiste el rumbo.",
    "Intentaste engañar al sistema, pero el sistema te engañó a ti."
];

const giveUpBtnTexts = [
    "🏳️ Ya no puedo más",
    "🏳️ Botón de pánico",
    "🏳️ ¡Sácame de aquí!",
    "🏳️ Me rindo, YouTube gana"
];

function getRandomItem(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

// ==================== WIN / GIVE UP ====================

function showWinScreen() {
    if (state.timerInterval) clearInterval(state.timerInterval);
    const finalTime = document.getElementById('time-counter').textContent;
    
    playWinSound();
    
    document.getElementById('game-screen').style.display = 'none';
    document.getElementById('win-screen').style.display = 'block';
    document.getElementById('win-hops').textContent = state.hops;
    document.getElementById('win-time').textContent = finalTime;
    
    renderPath('win-path-visualizer');
}

function confirmGiveUp() {
    document.getElementById('confirm-modal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('confirm-modal').style.display = 'none';
}

// Cerrar modal con Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
});

function giveUp() {
    closeModal();
    if (state.timerInterval) clearInterval(state.timerInterval);
    const finalTime = document.getElementById('time-counter').textContent;
    
    playLoseSound();
    
    // Parar el reproductor
    document.getElementById('youtube-player').src = '';
    
    document.getElementById('game-screen').style.display = 'none';
    
    // Update Random Texts
    document.querySelector('#surrender-screen h1').innerHTML = getRandomItem(surrenderTitles);
    document.querySelector('#surrender-screen .end-subtitle').innerHTML = getRandomItem(surrenderSubtitles) + `<br><br>Duraste <strong id="surrender-hops" class="highlight">${state.hops}</strong> saltos y <strong id="surrender-time" style="color: #ffd600;">${finalTime}</strong> de tiempo antes de abandonar.`;
    
    document.getElementById('surrender-screen').style.display = 'block';
    
    // Rellenar datos de rendición (updated above too)
    document.getElementById('surrender-start-thumb').src = state.start.thumb;
    document.getElementById('surrender-start-title').textContent = state.start.title;
    document.getElementById('surrender-target-thumb').src = state.target.thumb;
    document.getElementById('surrender-target-title').textContent = state.target.title;
    
    renderPath('surrender-path-visualizer');
}
