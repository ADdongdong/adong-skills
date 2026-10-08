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

  if (!email) {
    printJson({
      status: "error",
      error: {
        code: "MISSING_INPUT",
        message: "必须提供 email 参数。用法: node request_quota_code.cjs --email <邮箱>",
        recoverable: true,
        recovery_hint: "请补充 --email <邮箱> 参数后重试",
      },
    });
    process.exit(1);
  }

  const client = new CWClient();
  const result = await client.request("/api/quota/send_code", { email });

  if (result.status === "error") {
    printJson(result);
    process.exit(1);
  }

  printJson({
    status: "ok",
    message: result.message || "验证码已发送",
    next_step: `请查收邮件获取验证码，然后运行 redeem_quota_code.cjs --email ${email} --code <验证码>`,
  });
}

main();
