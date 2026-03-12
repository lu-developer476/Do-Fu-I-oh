
let appState = {
  me: null,
  cards: [],
  roomCode: null,
  match: null,
};

const $ = (sel) => document.querySelector(sel);
const familyFilter = $('#family-filter');

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.message || 'Error inesperado');
  return data;
}

function renderCatalog() {
  const catalog = $('#catalog');
  const filter = familyFilter.value;
  const cards = appState.cards.filter((card) => !filter || card.family === filter);
  catalog.innerHTML = cards.map(card => `
    <article class="card">
      <img src="${card.image}" alt="${card.name}" />
      <h4>${card.name}</h4>
      <div class="meta">
        <span class="badge">${card.family}</span>
        <span class="badge">${card.stage}</span>
        <span class="badge">HP ${card.hp}</span>
        <span class="badge">PdC ${card.shell}</span>
        <span class="badge">PA ${card.action_points}</span>
        <span class="badge">PM ${card.movement_points}</span>
      </div>
      <p>${card.description}</p>
    </article>
  `).join('');
}

function laneCardHtml(cardState) {
  if (!cardState) return '<div class="small">Vacío</div>';
  const card = cardState.card;
  return `
    <div class="unit">
      <img src="${card.image}" alt="${card.name}" />
      <div>
        <strong>${card.name}</strong>
        <div class="small">HP ${cardState.current_hp} · PdC ${cardState.current_shell}</div>
        <div class="small">PA ${card.action_points} · PM ${card.movement_points} · ${cardState.can_attack ? 'Listo para atacar' : 'Fatigado'}</div>
      </div>
    </div>
  `;
}

function renderBoard() {
  const match = appState.match;
  if (!match) {
    $('#player-board').innerHTML = '<div class="small">Todavía no hay partida.</div>';
    $('#enemy-board').innerHTML = '<div class="small">Todavía no hay partida.</div>';
    $('#hand').innerHTML = '<div class="small">Tu mano aparecerá acá.</div>';
    $('#match-summary').innerHTML = '<div class="small">Crea o únete a una sala.</div>';
    $('#log').innerHTML = '';
    return;
  }
  const me = match.host.user_id === appState.me?.id ? match.host : match.guest;
  const enemy = match.host.user_id === appState.me?.id ? match.guest : match.host;
  const makeLanes = (player) => ['top','mid','bot'].map(lane => `
    <div class="lane">
      <div class="lane-label">${lane}</div>
      ${laneCardHtml(player?.board?.[lane])}
    </div>
  `).join('');

  $('#player-board').innerHTML = makeLanes(me);
  $('#enemy-board').innerHTML = makeLanes(enemy || {board:{}});
  $('#hand').innerHTML = (me?.hand || []).map((card, index) => `
    <article class="card">
      <img src="${card.image}" alt="${card.name}" />
      <h4>#${index} · ${card.name}</h4>
      <div class="meta">
        <span class="badge">HP ${card.hp}</span>
        <span class="badge">PdC ${card.shell}</span>
        <span class="badge">PA ${card.action_points}</span>
        <span class="badge">PM ${card.movement_points}</span>
      </div>
    </article>
  `).join('') || '<div class="small">No quedan cartas en mano.</div>';

  $('#match-summary').innerHTML = `
    <div><strong>Sala:</strong> ${appState.roomCode || '-'}</div>
    <div><strong>Turno:</strong> ${match.turn}</div>
    <div><strong>Ronda:</strong> ${match.turn_number}</div>
    <div><strong>Tu vida:</strong> ${me?.life ?? '-'} · <strong>Energía:</strong> ${me?.energy ?? '-'}/${me?.max_energy ?? '-'}</div>
    <div><strong>Vida rival:</strong> ${enemy?.life ?? '-'}</div>
    <div><strong>Biblioteca rival:</strong> ${enemy?.library_count ?? 0} · <strong>Mano rival:</strong> ${enemy?.hand_count ?? 0}</div>
    <div><strong>Ganador:</strong> ${match.winner || 'sin definir'}</div>
  `;
  $('#log').innerHTML = (match.log || []).slice().reverse().map(item => `<div class="log-item">${item}</div>`).join('');
}

async function loadCards() {
  const data = await api('/api/cards/');
  appState.cards = data.cards;
  const families = [...new Set(data.cards.map(card => card.family))];
  familyFilter.innerHTML = '<option value="">Todas las familias</option>' + families.map(f => `<option value="${f}">${f}</option>`).join('');
  renderCatalog();
}

async function authAction(kind) {
  const payload = {
    username: $('#username').value,
    email: $('#email').value,
    password: $('#password').value,
  };
  const data = await api(`/api/auth/${kind}/`, { method: 'POST', body: JSON.stringify(payload) });
  appState.me = data.user;
  $('#auth-status').textContent = `Sesión activa como ${data.user.username}.`;
}

async function loadProfile() {
  try {
    const data = await api('/api/auth/profile/');
    appState.me = data.user;
    $('#auth-status').textContent = `Sesión activa como ${data.user.username}.`;
  } catch {
    $('#auth-status').textContent = 'Todavía no iniciaste sesión.';
  }
}

async function createMatch() {
  const data = await api('/api/match/create/', { method: 'POST', body: '{}' });
  appState.roomCode = data.room_code;
  appState.match = data.match;
  renderBoard();
}

async function joinMatch() {
  const code = $('#join-room-code').value.trim().toUpperCase();
  const data = await api(`/api/match/${code}/join/`, { method: 'POST', body: '{}' });
  appState.roomCode = data.room_code;
  appState.match = data.match;
  renderBoard();
}

async function refreshMatch() {
  if (!appState.roomCode) return;
  const data = await api(`/api/match/${appState.roomCode}/`);
  appState.match = data.match;
  renderBoard();
}

async function action(kind) {
  if (!appState.roomCode) return alert('Primero crea o únete a una sala.');
  const payload = {
    action: kind,
    hand_index: Number($('#hand-index').value),
    lane: $('#lane-select').value,
    from_lane: $('#from-lane').value,
    target_lane: $('#target-lane').value,
  };
  const data = await api(`/api/match/${appState.roomCode}/action/`, { method: 'POST', body: JSON.stringify(payload) });
  appState.match = data.match;
  renderBoard();
}

$('#register-btn').addEventListener('click', () => authAction('register').catch(err => alert(err.message)));
$('#login-btn').addEventListener('click', () => authAction('login').catch(err => alert(err.message)));
$('#logout-btn').addEventListener('click', async () => { await api('/api/auth/logout/', { method: 'POST', body: '{}' }); appState.me = null; $('#auth-status').textContent = 'Sesión cerrada.'; });
$('#create-match').addEventListener('click', () => createMatch().catch(err => alert(err.message)));
$('#join-match').addEventListener('click', () => joinMatch().catch(err => alert(err.message)));
$('#refresh-state').addEventListener('click', () => refreshMatch().catch(err => alert(err.message)));
$('#summon-btn').addEventListener('click', () => action('summon').catch(err => alert(err.message)));
$('#move-btn').addEventListener('click', () => action('move').catch(err => alert(err.message)));
$('#attack-btn').addEventListener('click', () => action('attack').catch(err => alert(err.message)));
$('#end-turn-btn').addEventListener('click', () => action('end_turn').catch(err => alert(err.message)));
familyFilter.addEventListener('change', renderCatalog);

loadCards().then(loadProfile).then(renderBoard);
