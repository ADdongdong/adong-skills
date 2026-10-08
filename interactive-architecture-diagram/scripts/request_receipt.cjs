const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

function writeRecord(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const temporary = `${file}.${crypto.randomBytes(6).toString("hex")}.tmp`;
  try {
    fs.writeFileSync(temporary, JSON.stringify(value, null, 2), { encoding: "utf8", mode: 0o600 });
    fs.renameSync(temporary, file);
  } finally {
    if (fs.existsSync(temporary)) fs.unlinkSync(temporary);
  }
}

async function withRequestReceipt(client, endpoint, execute) {
  const invalid = client.validateBaseUrl();
  if (invalid) return invalid;
  const headers = client.headers();
  if (!["/run", "/session/edit/browser"].includes(endpoint)) return execute(headers);
  const requestId = headers["X-Request-ID"];
  const token = crypto.randomBytes(32).toString("hex");
  headers["X-Request-Token"] = token;
  const file = path.join(process.cwd(), ".cw_skill", "requests", `${requestId}.receipt.json`);
  // Keep credentials and original business input out of the request journal.
  const record = { request_id: requestId, request_token: token, endpoint,
    created_at: new Date().toISOString(), state: "pending" };
  try {
    writeRecord(file, record);
  } catch (error) {
    return client.error("RECEIPT_SAVE_FAILED", "无法保存请求记录，本次尚未提交；请检查工作目录写入权限。", true);
  }
  process.stderr.write(`[ContextWeave] 请求记录：${file}\n`);
  const result = await execute(headers);
  record.state = result.receipt ? result.receipt.status : "unconfirmed";
  record.result = result;
  record.updated_at = new Date().toISOString();
  try {
    writeRecord(file, record);
  } catch (error) {
    result.warnings = [...(result.warnings || []), "结果回执未能写回本地；初始请求号已保存，可查询服务端记录。"];
  }
  result.request_id = requestId;
  result.saved_request_record = file;
  if (!result.receipt && result.status === "error") {
    result.error = { ...result.error, recovery_hint:
      `执行与扣次状态尚未确认。先运行 node scripts/query_request.cjs --record "${file}" 查询原请求，再决定是否重新提交。` };
  }
  return result;
}

module.exports = { writeRecord, withRequestReceipt };
