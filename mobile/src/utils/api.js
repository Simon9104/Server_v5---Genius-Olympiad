/**
 * GreenIOT API utilities
 * All functions accept baseUrl as the first argument (e.g. "http://192.168.1.10:8080")
 */

/**
 * Internal helper — fetch with a 5-second timeout.
 */
async function fetchWithTimeout(url, options = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * GET /data — returns sensor readings for all Picos.
 * Expected shape: { picos: [ { id, name, humidity, temperature, door, pump, ram }, ... ] }
 */
export async function fetchData(baseUrl) {
  const response = await fetchWithTimeout(`${baseUrl}/data`);
  return response.json();
}

/**
 * GET /alerts — returns list of ThingSpeak failure events.
 * Expected shape: [ { time, msg }, ... ]
 */
export async function fetchAlerts(baseUrl) {
  const response = await fetchWithTimeout(`${baseUrl}/alerts`);
  return response.json();
}

/**
 * GET /status — returns server status.
 * Expected shape: { started: string, uptime: string }
 */
export async function fetchStatus(baseUrl) {
  const response = await fetchWithTimeout(`${baseUrl}/status`);
  return response.json();
}

/**
 * POST /door — send a door command to a specific Pico.
 * @param {string} baseUrl
 * @param {number} picoId  — 1, 2, or 3
 * @param {1|0|null} value — 1 = open, 0 = close, null = auto
 */
export async function sendDoor(baseUrl, picoId, value) {
  const response = await fetchWithTimeout(`${baseUrl}/door`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pico: picoId, value }),
  });
  return response.json();
}
