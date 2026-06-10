import { getStore } from "@netlify/blobs";

export default async (req, context) => {
  const store = getStore("greeniot");
  const data = await store.get("latest", { type: "json" }).catch(() => null);
  const cors = { "access-control-allow-origin": "*", "content-type": "application/json" };
  return new Response(JSON.stringify({
    last_sync: data?.synced_at || null,
    has_data: !!data,
  }), { headers: cors });
};
export const config = { path: "/api/status" };
