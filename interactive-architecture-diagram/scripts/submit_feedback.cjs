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
  const sessionId = args["--session_id"] || args["-s"];
  const category = args["--category"] || args["-c"];
  const userComplaint = args["--user_complaint"] || args["-u"];
  const agentAnalysis = args["--agent_analysis"] || args["-a"];

  if (!sessionId) {
    printJson({
      status: "error",
      error: {
        code: "MISSING_INPUT",
        message: "必须提供 session_id",
        recoverable: true,
        recovery_hint: "请补充 session_id 参数后重试",
      },
    });
    process.exit(1);
  }

  const payload = {
    session_id: sessionId,
    category: category || "general",
    user_complaint: userComplaint || "",
    agent_analysis: agentAnalysis || ""
  };

  const client = new CWClient();
  const result = await client.request("/api/feedback", payload);

  printJson(result);
  if (result.status === "error") {
    process.exit(1);
  }
}

main();