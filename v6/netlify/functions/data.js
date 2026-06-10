import { getStore } from "@netlify/blobs";

export default async (req, context) => {
  const store = getStore("greeniot");
  const data = await store.get("latest", { type: "json" });
  if (!data) {
    return new Response(JSON.stringify({ error: "No data yet" }), {
      status: 404, headers: { "content-type": "application/json", "access-control-allow-origin": "*" }
    });
  }
  return new Response(JSON.stringify(data), {
    headers: { "content-type": "application/json", "access-control-allow-origin": "*" }
  });
};
export const config = { path: "/api/data" };
