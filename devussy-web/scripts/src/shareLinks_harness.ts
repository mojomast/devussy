/*
 * Lightweight CLI harness for shareLinks helpers.
 *
 * Usage (from devussy-web/):
 *   npx ts-node -r tsconfig-paths/register --project tsconfig.scripts.json \
 *     scripts/src/shareLinks_harness.ts roundtrip <stage> '<json-data>'
 *   npx ts-node -r tsconfig-paths/register --project tsconfig.scripts.json \
 *     scripts/src/shareLinks_harness.ts decode <encoded>
 */

import { generateShareLink, decodeSharePayload } from "@/shareLinks";

function toJson(value: unknown): string {
  return JSON.stringify(value);
}

async function main() {
  const [cmd, ...rest] = process.argv.slice(2);

  if (cmd === "roundtrip") {
    const stage = rest[0];
    const jsonArg = rest[1] || "{}";

    if (!stage) {
      // eslint-disable-next-line no-console
      console.error("Usage: roundtrip <stage> '<json-data>'");
      process.exit(1);
    }

    let data: any = {};
    try {
      data = JSON.parse(jsonArg);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error("Invalid JSON data:", err);
      process.exit(1);
    }

    const url = generateShareLink(stage, data);

    let encoded: string | null = null;
    try {
      const base = "http://localhost";
      const parsed = new URL(url, base);
      encoded = parsed.searchParams.get("payload");
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error("Failed to parse generated URL:", err);
      process.exit(1);
    }

    const decoded = encoded ? decodeSharePayload(encoded) : null;

    const output = {
      url,
      encoded,
      decoded,
    };

    // eslint-disable-next-line no-console
    console.log(toJson(output));
    return;
  }

  if (cmd === "decode") {
    const encoded = rest[0] || "";
    const decoded = decodeSharePayload(encoded);
    // eslint-disable-next-line no-console
    console.log(toJson(decoded));
    return;
  }

  // eslint-disable-next-line no-console
  console.error("Unknown command. Use 'roundtrip' or 'decode'.");
  process.exit(1);
}

void main();
