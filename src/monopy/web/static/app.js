// State management
let lobbyCode = null;
let playerId = null;
let playerName = null;
let socket = null;
let lastPhase = null;
let lastDiceRoll = null;

// Player Tokens config
const TOKENS = ["🎩", "🚗", "🐕", "🚢", "🦖", "💡", "🏎️", "🐈"];

// DOM Elements
const screens = {
  lobby: document.getElementById("lobby-screen"),
  game: document.getElementById("game-screen")
};

const lobbyInputs = {
  createName: document.getElementById("create-player-name"),
  joinName: document.getElementById("join-player-name"),
  joinCode: document.getElementById("join-lobby-code")
};

const buttons = {
  createLobby: document.getElementById("btn-create-lobby"),
  joinLobby: document.getElementById("btn-join-lobby"),
  copyCode: document.getElementById("btn-copy-code"),
  startGame: document.getElementById("btn-start-game"),
  sendChat: document.getElementById("btn-send-chat")
};

const display = {
  lobbyCode: document.getElementById("display-lobby-code"),
  playerCount: document.getElementById("display-player-count"),
  playersList: document.getElementById("players-list"),
  logs: document.getElementById("game-logs"),
  chatMessages: document.getElementById("chat-messages"),
  board: document.getElementById("monopoly-board")
};

const chatInput = document.getElementById("chat-input");
const pregameControls = document.getElementById("lobby-pregame-controls");

// Modal Elements
const modal = document.getElementById("decision-modal");
const modalTitle = document.getElementById("modal-title");
const modalBody = document.getElementById("modal-body");
const modalActions = document.getElementById("modal-actions");

// 1. Keep track of audio context and the master gain globally
let audioCtx = null;
let masterGain = null;
let currentVolume = 0.5;

function initAudio() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();

    masterGain = audioCtx.createGain();
    masterGain.connect(audioCtx.destination);

    masterGain.gain.setValueAtTime(currentVolume, audioCtx.currentTime)
  }

  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
}

// Safely attach the event listener ONLY after the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
  const slider = document.getElementById('volumeSlider');

  // The 'if' check prevents errors if the slider isn't on the current screen
  if (slider) {
    slider.addEventListener('input', (event) => {
      currentVolume = parseFloat(event.target.value);
      if (masterGain && audioCtx) {
        masterGain.gain.linearRampToValueAtTime(currentVolume, audioCtx.currentTime + 0.01);
      }
    });
  }
});

// Web Audio API Sound synthesizers
function playSound(type) {
  try {
    initAudio();

    // const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const time = audioCtx.currentTime;

    if (type === "dice") {
      // Dice rolling clicks
      for (let i = 0; i < 6; i++) {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain);

        gain.connect(masterGain);

        osc.frequency.setValueAtTime(150 + Math.random() * 200, time + (i * 0.08));
        gain.gain.setValueAtTime(0.1, time + (i * 0.08));
        gain.gain.exponentialRampToValueAtTime(0.001, time + (i * 0.08) + 0.06);

        osc.start(time + (i * 0.08));
        osc.stop(time + (i * 0.08) + 0.06);
      }
    } else if (type === "cash") {
      // Ding ding cash sound
      const osc1 = audioCtx.createOscillator();
      const osc2 = audioCtx.createOscillator();
      const gain = audioCtx.createGain();

      osc1.type = "sine";
      osc2.type = "sine";
      osc1.frequency.setValueAtTime(880, time);
      osc2.frequency.setValueAtTime(1320, time + 0.08);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(masterGain);

      gain.gain.setValueAtTime(0.12, time);
      gain.gain.exponentialRampToValueAtTime(0.001, time + 0.4);

      osc1.start(time);
      osc2.start(time + 0.08);
      osc1.stop(time + 0.4);
      osc2.stop(time + 0.4);
    } else if (type === "jail") {
      // Buzzer sound
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(80, time);
      osc.connect(gain);
      gain.connect(masterGain);
      gain.gain.setValueAtTime(0.15, time);
      gain.gain.exponentialRampToValueAtTime(0.001, time + 0.3);
      osc.start(time);
      osc.stop(time + 0.3);
    }
  } catch (e) {
    console.warn("Sound play failed", e);
  }
}

// Show/Hide Screens
function showScreen(screenId) {
  Object.keys(screens).forEach(key => {
    if (key === screenId) {
      screens[key].classList.add("active");
    } else {
      screens[key].classList.remove("active");
    }
  });
}

// Copy Lobby Code
buttons.copyCode.addEventListener("click", () => {
  if (lobbyCode) {
    navigator.clipboard.writeText(lobbyCode);
    alert("Lobby code copied to clipboard: " + lobbyCode);
  }
});

// Event Listeners for REST endpoints
buttons.createLobby.addEventListener("click", async () => {
  const name = lobbyInputs.createName.value.trim();
  if (!name) return alert("Please enter your name");

  try {
    const res = await fetch("/api/lobby/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ creator_name: name })
    });
    const data = await res.json();

    lobbyCode = data.lobby_code;
    playerId = data.player_id;
    playerName = data.player_name;

    setupLobbyUI();
    connectWebSocket();
  } catch (e) {
    alert("Error creating lobby: " + e.message);
  }
});

buttons.joinLobby.addEventListener("click", async () => {
  const name = lobbyInputs.joinName.value.trim();
  const code = lobbyInputs.joinCode.value.trim().toUpperCase();

  if (!name) return alert("Please enter your name");
  if (!code) return alert("Please enter a lobby code");

  try {
    const res = await fetch("/api/lobby/join", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lobby_code: code, player_name: name })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Join failed");
    }

    const data = await res.json();
    lobbyCode = data.lobby_code;
    playerId = data.player_id;
    playerName = data.player_name;

    setupLobbyUI();
    connectWebSocket();
  } catch (e) {
    alert("Error joining lobby: " + e.message);
  }
});

function setupLobbyUI() {
  display.lobbyCode.textContent = lobbyCode;
  showScreen("game");
}

// Connect to WebSocket Server
function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  const wsUrl = `${protocol}//${host}/ws/lobby/${lobbyCode}/${playerId}`;

  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log("WebSocket connected to " + wsUrl);
  };

  socket.onmessage = (event) => {
    const payload = JSON.parse(event.data);
    if (payload.type === "state_update") {
      renderLobby(payload.data);
    }
  };

  socket.onclose = (event) => {
    console.log("WebSocket disconnected", event);
    alert("Connection to game server lost. Reconnect to play again.");
    showScreen("lobby");
  };
}

// Main state render loop from WebSocket data
function renderLobby(data) {
  const isCreator = data.creator_id === playerId;
  display.playerCount.textContent = `${data.players.length}/8`;

  // 1. Render Pregame Lobby start button
  if (data.status === "LOBBY") {
    pregameControls.classList.remove("hide");
    if (isCreator && data.players.length >= 2) {
      buttons.startGame.classList.remove("hide");
      pregameControls.querySelector(".waiting-msg").classList.add("hide");
    } else {
      buttons.startGame.classList.add("hide");
      pregameControls.querySelector(".waiting-msg").classList.remove("hide");
      if (isCreator) {
        pregameControls.querySelector(".waiting-msg").textContent = "Waiting for at least 2 players to join...";
      }
    }
  } else {
    pregameControls.classList.add("hide");
  }

  // 2. Render Players side-panel list
  renderPlayersList(data.players, data.game_state);

  // 3. Render Logs
  if (data.game_state) {
    renderLogs(data.game_state.history);

    // Trigger sounds on updates
    if (lastPhase !== data.game_state.phase) {
      if (data.game_state.phase === "JAIL_DECISION") {
        playSound("jail");
      }
      lastPhase = data.game_state.phase;
    }

    if (JSON.stringify(lastDiceRoll) !== JSON.stringify(data.game_state.last_roll)) {
      if (data.game_state.last_roll) playSound("dice");
      lastDiceRoll = data.game_state.last_roll;
    }
  }

  // 4. Render Chat
  renderChatMessages(data.chat_messages);

  // 5. Render Board
  if (data.game_state) {
    renderBoard(data.game_state.board, data.players, data.game_state.current_player_index);
    renderCenterPanel(data);
  } else {
    renderPregameBoard();
  }
}

function renderPlayersList(players, gameState) {
  display.playersList.innerHTML = "";
  players.forEach((p, idx) => {
    const isActive = gameState && gameState.current_player_index === idx;
    const playerRow = document.createElement("div");
    playerRow.className = `player-row ${isActive ? "active" : ""}`;

    const tokenEmoji = TOKENS[idx % TOKENS.length];

    playerRow.innerHTML = `
            <div class="player-avatar">${tokenEmoji}</div>
            <div class="player-info">
                <div class="player-name-wrapper">
                    <span class="player-name">${p.name} ${p.id === playerId ? "(You)" : ""}</span>
                    <span class="online-dot ${p.is_online ? "online" : ""}" title="${p.is_online ? 'Online' : 'Offline'}"></span>
                </div>
                <div class="player-cash">$${p.balance}</div>
            </div>
            ${p.in_jail ? `<span class="player-jail-badge"><i class="fa-solid fa-lock"></i> Jail</span>` : ""}
        `;

    display.playersList.appendChild(playerRow);
  });
}

function renderLogs(history) {
  display.logs.innerHTML = "";
  // Show newest first
  const reversed = [...history].reverse();
  reversed.forEach(log => {
    const entry = document.createElement("div");
    entry.className = "log-entry";
    entry.innerHTML = log;
    display.logs.appendChild(entry);
  });
}

function renderChatMessages(messages) {
  display.chatMessages.innerHTML = "";
  messages.forEach(msg => {
    const bubble = document.createElement("div");
    const isSystem = msg.player_name === "System";
    const isMe = msg.player_name === playerName;

    bubble.className = `chat-bubble ${isSystem ? 'system' : (isMe ? 'me' : 'user')}`;

    if (isSystem) {
      bubble.textContent = msg.text;
    } else {
      bubble.innerHTML = `
                <div class="chat-sender">${msg.player_name}</div>
                <div>${msg.text}</div>
            `;
    }
    display.chatMessages.appendChild(bubble);
  });
  display.chatMessages.scrollTop = display.chatMessages.scrollHeight;
}

// Initial board rendering before game starts
function renderPregameBoard() {
  display.board.innerHTML = `
        <div class="board-center">
            <div class="center-title">MONOPOLY</div>
            <p style="color: var(--text-secondary); max-width: 250px; text-align: center; font-size: 0.9rem;">
                Create or join a lobby, and wait for the host to start the game!
            </p>
        </div>
    `;

  // Add corners and placeholders to look like a board
  for (let i = 0; i < 40; i++) {
    const isCorner = i % 10 === 0;
    const space = document.createElement("div");
    space.className = `space space-${i} ${isCorner ? "corner" : ""}`;
    if (isCorner) {
      let label = "GO";
      if (i === 10) label = "JAIL";
      if (i === 20) label = "FREE PARK";
      if (i === 30) label = "GO JAIL";
      space.innerHTML = `<div class="space-name">${label}</div>`;
    } else {
      space.innerHTML = `<div class="space-name">Tile ${i}</div>`;
    }
    display.board.appendChild(space);
  }
}

// Render dynamic game board with owner colors and active player tokens
function renderBoard(spaces, players, currentPlayerIndex) {
  // Save center panel if exists
  const centerPanel = display.board.querySelector(".board-center");
  display.board.innerHTML = "";
  if (centerPanel) {
    display.board.appendChild(centerPanel);
  }

  spaces.forEach(s => {
    const isCorner = s.index % 10 === 0;
    const spaceDiv = document.createElement("div");
    spaceDiv.className = `space space-${s.index} ${isCorner ? "corner" : ""}`;

    // Ownership styling
    if (s.owner_id) {
      const ownerIdx = players.findIndex(p => p.id === s.owner_id);
      if (s.owner_id === playerId) {
        spaceDiv.classList.add("owned-by-me");
      } else {
        spaceDiv.classList.add("owned-by-other");
      }
    }

    // Inside components
    let innerHtml = "";

    if (s.color_group && !isCorner) {
      innerHtml += `<div class="space-color-bar" style="background-color: var(--group-${s.color_group});"></div>`;
    }

    // Name
    innerHtml += `<div class="space-name">${s.name}</div>`;

    // Price / Owner marker
    if (s.price && !isCorner && !s.owner_id) {
      innerHtml += `<div class="space-price">$${s.price}</div>`;
    } else if (s.owner_id) {
      const ownerIdx = players.findIndex(p => p.id === s.owner_id);
      const ownerEmoji = TOKENS[ownerIdx % TOKENS.length];
      innerHtml += `<div class="space-price" style="color: #a5b4fc; font-weight: bold;">Owner: ${ownerEmoji}</div>`;
    }

    // Tokens container
    innerHtml += `<div class="tokens-container" id="tokens-${s.index}"></div>`;

    spaceDiv.innerHTML = innerHtml;
    display.board.appendChild(spaceDiv);
  });

  // Place tokens on their board coordinates
  players.forEach((p, idx) => {
    if (p.balance < 0) return; // bankrupted players are eliminated
    const tokenContainer = document.getElementById(`tokens-${p.position}`);
    if (tokenContainer) {
      const tokenSpan = document.createElement("span");
      tokenSpan.className = "token";
      tokenSpan.title = p.name;
      tokenSpan.textContent = TOKENS[idx % TOKENS.length];
      tokenContainer.appendChild(tokenSpan);
    }
  });
}

function renderCenterPanel(data) {
  const gm = data.game_state;
  let centerDiv = display.board.querySelector(".board-center");

  if (!centerDiv) {
    centerDiv = document.createElement("div");
    centerDiv.className = "board-center";
    display.board.appendChild(centerDiv);
  }

  const activePlayer = data.players[gm.current_player_index];
  const isMyTurn = activePlayer.id === playerId;

  // Status text
  let statusLabel = "Current Turn";
  let statusVal = activePlayer.name;

  if (gm.phase === "GAME_OVER") {
    statusLabel = "🎉 Game Finished!";
    statusVal = `${gm.winner_name} Wins!`;
  } else if (isMyTurn) {
    statusVal = "🌟 Your Turn! 🌟";
  }

  // Dice
  const rollData = gm.last_roll || [1, 1];

  centerDiv.innerHTML = `
        <div class="center-title">MONOPOLY</div>
        
        <div class="status-area">
            <div class="status-label">${statusLabel}</div>
            <div class="status-value">${statusVal}</div>
            <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 4px;">
                Phase: <span style="color: #f3f4f6; font-weight: bold;">${gm.phase}</span>
            </div>
        </div>
        
        <div class="dice-container">
            <div class="die" id="die1">${rollData[0]}</div>
            <div class="die" id="die2">${rollData[1]}</div>
        </div>
        
        <div class="center-actions">
            ${renderActionButtons(gm.phase, isMyTurn, activePlayer, gm.board[activePlayer.position])}
        </div>
    `;

  // Trigger modal if my turn and decision is pending
  if (isMyTurn && gm.phase === "BUY_DECISION") {
    const activeSpace = gm.board[activePlayer.position];
    showBuyModal(activeSpace);
  } else {
    modal.classList.add("hide");
  }
}

function renderActionButtons(phase, isMyTurn, activePlayer, currentSpace) {
  if (phase === "GAME_OVER") {
    return `<p style="text-align: center; color: var(--accent-secondary); font-weight: bold;">Game Finished!</p>`;
  }

  if (!isMyTurn) {
    return `<p style="text-align: center; color: var(--text-secondary); font-size: 0.9rem;">Waiting for ${activePlayer.name}...</p>`;
  }

  if (phase === "ROLL") {
    return `<button id="btn-roll" class="btn btn-primary btn-block"><i class="fa-solid fa-dice"></i> Roll Dice</button>`;
  }

  if (phase === "JAIL_DECISION") {
    return `
            <button id="btn-roll" class="btn btn-primary btn-block" style="margin-bottom: 8px;"><i class="fa-solid fa-dice"></i> Roll for Doubles</button>
            <button id="btn-pay-fine" class="btn btn-secondary btn-block" ${activePlayer.balance < 50 ? 'disabled' : ''}><i class="fa-solid fa-wallet"></i> Pay $50 Fine</button>
        `;
  }

  if (phase === "BUY_DECISION") {
    return `<p style="text-align: center; color: var(--text-secondary); font-size: 0.9rem;">Decision pending...</p>`;
  }

  if (phase === "END_TURN") {
    return `<button id="btn-end-turn" class="btn btn-secondary btn-block"><i class="fa-solid fa-right-from-bracket"></i> End Turn</button>`;
  }

  return "";
}

// Hook actions from controls
document.addEventListener("click", (e) => {
  if (!socket || socket.readyState !== WebSocket.OPEN) return;

  if (e.target.id === "btn-roll" || e.target.closest("#btn-roll")) {
    // Play quick local animation
    document.getElementById("die1")?.classList.add("rolling");
    document.getElementById("die2")?.classList.add("rolling");
    setTimeout(() => {
      sendAction("roll_dice");
    }, 300);
  } else if (e.target.id === "btn-pay-fine" || e.target.closest("#btn-pay-fine")) {
    sendAction("pay_fine");
  } else if (e.target.id === "btn-end-turn" || e.target.closest("#btn-end-turn")) {
    sendAction("end_turn");
  } else if (e.target.id === "btn-modal-buy") {
    playSound("cash");
    sendAction("buy_property");
    modal.classList.add("hide");
  } else if (e.target.id === "btn-modal-pass") {
    sendAction("pass_property");
    modal.classList.add("hide");
  }
});

function showBuyModal(space) {
  modalTitle.textContent = "Buy Property?";
  modalBody.innerHTML = `
        <p>Would you like to purchase this property?</p>
        <div class="property-card-view">
            <div class="property-card-header" style="background-color: var(--group-${space.color_group || 'slate'});"></div>
            <div class="property-card-title">${space.name}</div>
            <div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 8px;">${space.space_type}</div>
            <div class="property-card-price">$${space.price}</div>
        </div>
    `;
  modalActions.innerHTML = `
        <button id="btn-modal-buy" class="btn btn-primary"><i class="fa-solid fa-cart-shopping"></i> Buy ($${space.price})</button>
        <button id="btn-modal-pass" class="btn btn-secondary">Pass</button>
    `;
  modal.classList.remove("hide");
}

function sendAction(action, extra = {}) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ action, ...extra }));
  }
}

// Chat action listeners
buttons.sendChat.addEventListener("click", sendChatMessage);
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendChatMessage();
});

function sendChatMessage() {
  const text = chatInput.value.trim();
  if (!text) return;

  sendAction("chat", { text });
  chatInput.value = "";
}

// Pregame lobby start game trigger
buttons.startGame.addEventListener("click", () => {
  sendAction("start_game");
});
