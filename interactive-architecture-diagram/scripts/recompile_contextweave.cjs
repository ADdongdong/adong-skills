#!/usr/bin/env node
const { CWClient, normalizeAssetResult, downloadAssetsLocally, printJson } = require("./cw_client.cjs");

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

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const sessionId = args["--session_id"] || args["-s"];

  if (!sessionId) {
    printJson({
      status: "error",
      error: {
        code: "MISSING_REQUIRED_ARGS",
        message: "必须提供 session_id",
        recoverable: true,
        recovery_hint: "补充参数后重试",
      },
    });
    process.exit(1);
  }

  // 轮询预算：默认最长等待约 20 分钟，间隔 15s 起步、按 1.3 倍退避、封顶 60s
  const maxWaitMs =
    parseFloat(args["--max_wait_minutes"] || process.env.CW_RECOMPILE_MAX_WAIT_MINUTES || "20") * 60 * 1000;
  const baseIntervalMs =
    parseFloat(args["--interval"] || process.env.CW_RECOMPILE_INTERVAL_SECONDS || "15") * 1000;
  const maxIntervalMs = 60000;

  const client = new CWClient();
  const deadline = Date.now() + maxWaitMs;
  let attempt = 0;

  while (true) {
    attempt += 1;
    const result = normalizeAssetResult(await client.recompileSession(sessionId));

    if (result.status === "ok") {
      if (attempt > 1) {
        process.stderr.write(`[poll] 第 ${attempt} 次轮询成功，图表已生成。\n`);
      }
      await downloadAssetsLocally(result);
      printJson(result);
      if (result.status === "error") {
        process.exit(1);
      }
      return;
    }

    const code = (result.error || {}).code;

    // FILE_NOT_FOUND = 后端专家队列仍在处理，D2 文件尚未落盘 → 退避后继续轮询
    if (code === "FILE_NOT_FOUND") {
      const remainingMs = deadline - Date.now();
      if (remainingMs <= 0) {
        break;
      }
      const waitMs = Math.min(baseIntervalMs * Math.pow(1.3, attempt - 1), maxIntervalMs, remainingMs);
      process.stderr.write(
        `[poll ${attempt}] 后端深度处理中，${Math.round(waitMs / 1000)}s 后继续轮询（剩余预算约 ${Math.round(remainingMs / 60000)} 分钟）...\n`
      );
      await sleep(waitMs);
      continue;
    }

    // 其他错误（会话失效、导出失败等）立即退出，不做无谓重试
    printJson(result);
    process.exit(1);
  }

  printJson({
    status: "error",
    session_id: sessionId,
    error: {
      code: "RECOMPILE_POLL_TIMEOUT",
      message: `轮询等待超过预算（约 ${Math.round(maxWaitMs / 60000)} 分钟），后端仍未产出结果`,
      recoverable: true,
      recovery_hint:
        "可稍后再次运行本脚本拉取结果；若持续失败，请引导用户提供邮箱并调用 submit_feedback.cjs 上报",
    },
  });
  process.exit(1);
}

main();
