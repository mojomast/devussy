export interface ShareLinkPayload {
  stage: string;
  data: any;
}

function toBase64Url(base64: string): string {
  return base64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function fromBase64Url(base64url: string): string {
  const base = base64url.replace(/-/g, "+").replace(/_/g, "/");
  const padLength = base.length % 4 === 0 ? 0 : 4 - (base.length % 4);
  const padded = base + "=".repeat(padLength);
  return padded;
}

function encodeJsonToBase64Url(obj: any): string {
  const json = JSON.stringify(obj ?? {});

  if (typeof window === "undefined") {
    // Node / server-side
    // eslint-disable-next-line no-undef
    const base64 = Buffer.from(json, "utf8").toString("base64");
    return toBase64Url(base64);
  }

  const base64 = window.btoa(unescape(encodeURIComponent(json)));
  return toBase64Url(base64);
}

function decodeBase64UrlToJson(encoded: string): any {
  const base64 = fromBase64Url(encoded);

  if (typeof window === "undefined") {
    // Node / server-side
    // eslint-disable-next-line no-undef
    const json = Buffer.from(base64, "base64").toString("utf8");
    return JSON.parse(json);
  }

  const json = decodeURIComponent(escape(window.atob(base64)));
  return JSON.parse(json);
}

export function generateShareLink(stage: string, data: any): string {
  const payload: ShareLinkPayload = { stage, data };
  const encoded = encodeJsonToBase64Url(payload);

  if (typeof window === "undefined") {
    // Fallback: relative URL without origin when window is not available
    return `/share?payload=${encodeURIComponent(encoded)}`;
  }

  const origin = window.location.origin;
  return `${origin}/share?payload=${encodeURIComponent(encoded)}`;
}

export function decodeSharePayload(encoded: string): ShareLinkPayload | null {
  try {
    const obj = decodeBase64UrlToJson(encoded);
    if (!obj || typeof obj !== "object") return null;
    if (!("stage" in obj)) return null;
    return {
      stage: String((obj as any).stage),
      data: (obj as any).data,
    };
  } catch (err) {
    console.error("[shareLinks] Failed to decode share payload", err);
    return null;
  }
}
