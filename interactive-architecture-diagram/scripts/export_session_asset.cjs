#!/usr/bin/env node
const { CWClient, downloadAssetsLocally, printJson } = require("./cw_client.cjs");

const FORMAT_MAP = Object.freeze({
  svg: "svg",
  vsdx: "vsdx-native",
  "vsdx-native": "vsdx-native",
  pptx: "pptx-native",
  "pptx-native": "pptx-native",
  "pptx-svg": "pptx-svg",
  "pptx-legacy": "pptx",
});
const SUPPORTED_FORMATS = Object.freeze(Object.keys(FORMAT_MAP));

function resolveFormat(formatName) {
  return FORMAT_MAP[formatName] || null;
}

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("-")) {
      continue;
    }
    const next = argv[i + 1];
    const value = next && !next.startsWith("-") ? next : "true";
    args[token] = value;
    if (value !== "true") {
      i += 1;
    }
  }
  return args;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const sessionId = args["--session_id"] || args["-s"];
  const formatName = args["--format"] || args["-f"];
  const outputName = args["--output_name"] || args["-n"];
  const outputDir = args["--output_dir"] || args["-o"];

  if (!sessionId || !formatName) {
    printJson({
      status: "error",
      error: {
        code: "MISSING_REQUIRED_ARGS",
        message: "必须提供 session_id 和 format",
        recoverable: true,
        recovery_hint: "补充参数后重试",
      },
    });
    process.exit(1);
  }

  const backendFormat = resolveFormat(formatName);
  if (!backendFormat) {
    printJson({
      status: "error",
      error: {
        code: "INVALID_FORMAT",
        message: `format 仅支持 ${SUPPORTED_FORMATS.join("、")}`,
        recoverable: true,
        recovery_hint: "普通 Visio 使用 vsdx（默认原生）；普通 PPTX 使用 pptx（默认原生）；视觉保真优先使用 pptx-svg；旧版链路使用 pptx-legacy",
      },
    });
    process.exit(1);
  }

  const client = new CWClient();
  let result = await client.exportSessionAsset(sessionId, backendFormat);
  if (result.status === "error") {
    const message = String((result.error || {}).message || "");
    if (message.toLowerCase().includes("session")) {
      result = {
        status: "error",
        error: {
          code: "SESSION_INVALID_OR_EXPIRED",
          message: message || "session_id 无效或已过期",
          recoverable: true,
          recovery_hint: "请先重新生成以获取新的 session_id",
        },
      };
    }
  }

  if (result.status === "ok") {
    result.format = result.format || backendFormat;
    result.requested_format = formatName;
    result.output_name = outputName;
    result.output_dir = outputDir;
  }
  await downloadAssetsLocally(result);

  printJson(result);
  if (result.status === "error") {
    process.exit(1);
  }
}

module.exports = { FORMAT_MAP, SUPPORTED_FORMATS, resolveFormat };

if (require.main === module) {
  main();
}
