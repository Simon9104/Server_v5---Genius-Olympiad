  // ── Tab switcher ─────────────────────────────────────────────────────────
  function switchTab(e, id) {
    const parent = e.target.closest('.step-body');
    parent.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    parent.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    e.target.classList.add('active');
    parent.querySelector('#' + id).classList.add('active');
  }

  // ── Live dashboard ────────────────────────────────────────────────────────
  let pollTimer = null;
  const POLL_INTERVAL = 5000; // ms

  function ramColor(pct) {
    if (pct === null || pct === undefined) return 'var(--muted)';
    if (pct < 60) return 'var(--green)';
    if (pct < 80) return 'var(--yellow)';
    return 'var(--red)';
  }

  function updateCard(pico, i) {
    const hm   = pico.humidity    != null ? pico.humidity.toFixed(1)    : '—';
    const tp   = pico.temperature != null ? pico.temperature.toFixed(1) : '—';
    const ram  = pico.ram         != null ? pico.ram.toFixed(1)         : null;

    document.getElementById(`hm-${i}`).textContent     = hm;
    document.getElementById(`tp-${i}`).textContent     = tp;
    document.getElementById(`hm-bar-${i}`).style.width = pico.humidity    != null ? Math.min(pico.humidity, 100) + '%' : '0%';
    document.getElementById(`tp-bar-${i}`).style.width = pico.temperature != null ? Math.min(pico.temperature / 50 * 100, 100) + '%' : '0%';

    // Door
    const doorEl = document.getElementById(`door-${i}`);
    doorEl.textContent = pico.door === 1 ? 'OPEN' : pico.door === 0 ? 'CLOSED' : '—';
    doorEl.style.color = pico.door === 1 ? 'var(--green)' : 'var(--muted)';

    // Pump
    const pumpEl = document.getElementById(`pump-${i}`);
    pumpEl.textContent = pico.pump === 1 ? 'ON' : pico.pump === 0 ? 'OFF' : '—';
    pumpEl.style.color = pico.pump === 1 ? 'var(--green)' : 'var(--muted)';

    // RAM
    document.getElementById(`ram-val-${i}`).textContent   = ram ?? '—';
    document.getElementById(`ram-bar-${i}`).style.width   = ram != null ? ram + '%' : '0%';
    document.getElementById(`ram-bar-${i}`).style.background = ramColor(ram);

    // Ping badge — if we got data, pico is reachable
    const pingEl = document.getElementById(`ping-${i}`);
    pingEl.textContent = 'Online';
    pingEl.className = 'lc-ping online';

    // Flash card border
    const card = document.getElementById(`card-${i}`);
    card.classList.add('fresh');
    setTimeout(() => card.classList.remove('fresh'), 1000);
  }

  async function fetchData() {
    const host = document.getElementById('apiHost').value.trim();
    const url  = `http://${host}:8080/data`;
    const dot  = document.getElementById('liveDot');
    const txt  = document.getElementById('liveStatusText');
    const err  = document.getElementById('errorBanner');

    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(4000) });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      dot.className = 'live-dot online';
      txt.textContent = 'Connected';
      txt.style.color = 'var(--green)';
      err.style.display = 'none';

      data.picos.forEach((pico, i) => updateCard(pico, i));
      document.getElementById('lastUpdated').textContent =
        `Last updated: ${data.timestamp}  ·  refreshes every ${POLL_INTERVAL / 1000}s`;

    } catch (e) {
      dot.className = 'live-dot error';
      txt.textContent = 'Connection failed';
      txt.style.color = 'var(--red)';
      err.style.display = 'block';
      err.textContent = `Cannot reach ${url} — make sure server.py is running and the IP is correct. (${e.message})`;

      // Mark all picos offline
      for (let i = 0; i < 3; i++) {
        const pingEl = document.getElementById(`ping-${i}`);
        pingEl.textContent = 'Offline';
        pingEl.className = 'lc-ping offline';
      }
    }
  }

  async function sendDoor(picoId, value) {
    const host = document.getElementById('apiHost').value.trim();
    const url  = `http://${host}:8080/door`;
    const btns = document.querySelectorAll(`.door-controls button`);
    btns.forEach(b => b.disabled = true);
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pico: picoId, value: value }),
        signal: AbortSignal.timeout(4000),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const action = value === 1 ? 'Open' : value === 0 ? 'Close' : 'Auto';
      console.log(`Pico ${picoId} door → ${action}`);
    } catch (e) {
      alert(`Door command failed: ${e.message}`);
    } finally {
      btns.forEach(b => b.disabled = false);
    }
  }

  function startPolling() {
    stopPolling();
    fetchData();
    pollTimer = setInterval(fetchData, POLL_INTERVAL);
  }

  function stopPolling() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    document.getElementById('liveDot').className = 'live-dot';
    document.getElementById('liveStatusText').textContent = 'Stopped';
    document.getElementById('liveStatusText').style.color = 'var(--muted)';
  }
