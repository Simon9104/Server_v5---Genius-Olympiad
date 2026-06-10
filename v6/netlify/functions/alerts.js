import { getStore } from "@netlify/blobs";

export default async (req, context) => {
  const store = getStore("greeniot");
  const cors = { "access-control-allow-origin": "*", "content-type": "application/json" };

  if (req.method === "GET") {
    const alerts = await store.get("alerts", { type: "json" }).catch(() => []);
    return new Response(JSON.stringify(alerts || []), { headers: cors });
  }

  if (req.method === "POST") {
    const token = req.headers.get("x-greeniot-token");
    if (token !== process.env.GREENIOT_TOKEN) return new Response("Unauthorized", { status: 401 });
    const body = await req.json();
    const current = await store.get("alerts", { type: "json" }).catch(() => []);
    const updated = [...(current || []), body].slice(-100);
    await store.setJSON("alerts", updated);
    return new Response(JSON.stringify({ ok: true }), { headers: cors });
  }
};
export const config = { path: "/api/alerts" };
