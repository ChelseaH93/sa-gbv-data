const CONFIG_PATH = "/config.js";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === CONFIG_PATH) {
      const baseUrl = (env.R2_BASE_URL || "").trim().replace(/\/$/, "");
      return new Response(
        `window.SA_GBV_CONFIG = ${JSON.stringify({ R2_BASE_URL: baseUrl })};\n`,
        {
          headers: {
            "cache-control": "no-store",
            "content-type": "application/javascript; charset=utf-8"
          }
        }
      );
    }
    return env.ASSETS.fetch(request);
  }
};