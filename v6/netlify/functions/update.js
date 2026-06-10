import { getStore } from "@netlify/blobs";

export default async (req, context) => {
  const token = req.headers.get("x-greeniot-token");
  if (token !== process.env.GREENIOT_TOKEN) {
    return new Response("Unauthorized", { status: 401 });
  }
  const body = await req.json();
  const store = getStore("greeniot");
  await store.setJSON("latest", { ...body, synced_at: new Date().toISOString() });
  return new Response(JSON.stringify({ ok: true }), {
    headers: { "content-type": "application/json" }
  });
};
export const config = { path: "/api/update" };
