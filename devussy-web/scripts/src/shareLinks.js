"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.generateShareLink = generateShareLink;
exports.decodeSharePayload = decodeSharePayload;
function toBase64Url(base64) {
    return base64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}
function fromBase64Url(base64url) {
    const base = base64url.replace(/-/g, "+").replace(/_/g, "/");
    const padLength = base.length % 4 === 0 ? 0 : 4 - (base.length % 4);
    const padded = base + "=".repeat(padLength);
    return padded;
}
function encodeJsonToBase64Url(obj) {
    const json = JSON.stringify(obj !== null && obj !== void 0 ? obj : {});
    if (typeof window === "undefined") {
        // Node / server-side
        // eslint-disable-next-line no-undef
        const base64 = Buffer.from(json, "utf8").toString("base64");
        return toBase64Url(base64);
    }
    const base64 = window.btoa(unescape(encodeURIComponent(json)));
    return toBase64Url(base64);
}
function decodeBase64UrlToJson(encoded) {
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
function generateShareLink(stage, data) {
    const payload = { stage, data };
    const encoded = encodeJsonToBase64Url(payload);
    if (typeof window === "undefined") {
        // Fallback: relative URL without origin when window is not available
        return `/share?payload=${encodeURIComponent(encoded)}`;
    }
    const origin = window.location.origin;
    return `${origin}/share?payload=${encodeURIComponent(encoded)}`;
}
function decodeSharePayload(encoded) {
    try {
        const obj = decodeBase64UrlToJson(encoded);
        if (!obj || typeof obj !== "object")
            return null;
        if (!("stage" in obj))
            return null;
        return {
            stage: String(obj.stage),
            data: obj.data,
        };
    }
    catch (err) {
        console.error("[shareLinks] Failed to decode share payload", err);
        return null;
    }
}
