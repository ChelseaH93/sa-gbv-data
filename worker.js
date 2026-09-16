const CONFIG_PATH = "/config.js";
const DATA_PATH = "/data/latest/processed";

function corsHeaders() {
  return {
    "access-control-allow-headers": "Range, Content-Type",
    "access-control-allow-methods": "GET, HEAD, OPTIONS",
    "access-control-allow-origin": "*",
    "access-control-expose-headers": "Accept-Ranges, Content-Length, Content-Range, Content-Type, ETag"
  };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === CONFIG_PATH) {
      return new Response(
        `window.SA_GBV_CONFIG = ${JSON.stringify({ R2_BASE_URL: `${url.origin}${DATA_PATH}` })};\n`,
        {
          headers: {
            "cache-control": "no-store",
            "content-type": "application/javascript; charset=utf-8"
          }
        }
      );
    }
    if (url.pathname === DATA_PATH || url.pathname.startsWith(`${DATA_PATH}/`)) {
      if (request.method === "OPTIONS") {
        return new Response(null, { headers: corsHeaders() });
      }
      const baseUrl = (env.R2_BASE_URL || "").trim().replace(/\/$/, "");
      if (!baseUrl) {
        return new Response("R2_BASE_URL is not configured", { status: 500 });
      }
      const objectPath = url.pathname.slice(DATA_PATH.length);
      const upstream = await fetch(`${baseUrl}${objectPath}${url.search}`, request);
      const headers = new Headers(upstream.headers);
      Object.entries(corsHeaders()).forEach(([name, value]) => headers.set(name, value));
      return new Response(upstream.body, {
        status: upstream.status,
        statusText: upstream.statusText,
        headers
      });
    }
    return env.ASSETS.fetch(request);
  }
};