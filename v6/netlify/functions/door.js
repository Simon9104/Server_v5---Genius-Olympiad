import { getStore } from "@netlify/blobs";

export default async (req, context) => {
  const store = getStore("greeniot");
  const cors = { "access-control-allow-origin": "*", "content-type": "application/json" };

  if (req.method === "OPTIONS") return new Response("", { headers: cors });

  if (req.method === "GET") {
    const picoId = new URL(req.url).searchParams.get("pico") || "1";
    const val = await store.get(`door-${picoId}`, { type: "json" }).catch(() => null);
    return new Response(JSON.stringify({ door: val ?? null }), { headers: cors });
  }

  if (req.method === "POST") {
    const token = req.headers.get("x-greeniot-token");
    if (token !== process.env.GREENIOT_TOKEN) return new Response("Unauthorized", { status: 401 });
    const body = await req.json();
    const pico = String(body.pico || "1");
    const value = body.value === undefined ? null : body.value;
    await store.setJSON(`door-${pico}`, value);
    return new Response(JSON.stringify({ ok: true }), { headers: cors });
  }

  return new Response("Method not allowed", { status: 405 });
};
export const config = { path: "/api/door" };
