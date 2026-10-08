#!/usr/bin/env node
const { CWClient, printJson } = require("./cw_client.cjs");

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("-")) {
      continue;
    }
    const key = token;
    const next = argv[i + 1];
    const value = next && !next.startsWith("-") ? next : "true";
    args[key] = value;
    if (value !== "true") {
      i += 1;
    }
  }
  return args;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const email = args["--email"] || args["-e"];
  const code = args["--code"] || args["-c"];

  if (!email || !code) {
    printJson({
      status: "error",
      error: {
        code: "MISSING_INPUT",
        message: "必须提供 email 和 code 参数。用法: node redeem_quota_code.cjs --email <邮箱> --code <验证码>",
        recoverable: true,
        recovery_hint: "请补充 --email <邮箱> 与 --code <验证码> 参数后重试",
      },
    });
    process.exit(1);
  }

  const client = new CWClient();
  const result = await client.request("/api/quota/redeem", { email, code });

  if (result.status === "error") {
    printJson(result);
    process.exit(1);
  }

  printJson({
    status: "ok",
    message: result.message || "API Key 已发送至您的邮箱",
    next_step: "请查收邮件获取 API Key，并按指引将 CONTEXTWEAVE_MCP_API_KEY 配置到环境变量后重试生成",
  });
}

main();
