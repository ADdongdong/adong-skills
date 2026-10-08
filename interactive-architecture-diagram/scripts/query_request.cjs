#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const { CWClient, normalizeAssetResult, downloadAssetsLocally, printJson } = require("./cw_client.cjs");
const { writeRecord } = require("./request_receipt.cjs");

async function main(argv = process.argv.slice(2), Client = CWClient) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith("--")) args[argv[i].slice(2)] = argv[i+1] && !argv[i+1].startsWith("--") ? argv[++i] : true;
  }
  const client = new Client();
  let record = {};
  if (typeof args.record === "string") record = JSON.parse(fs.readFileSync(args.record, "utf8"));
  const requestId = args.request_id || record.request_id;
  if (!requestId && !args.list) throw new Error("请提供 --record <回执文件>、--request_id <请求号> 或 --list");
  const response = await client.getRequestReceipt({ requestId, token: record.request_token });
  if (args.list || !response.result) {
    printJson(response);
    return response;
  }
  const result = response.result;
  if (args.record) writeRecord(args.record, { ...record, state: response.receipt.status, result, updated_at: new Date().toISOString() });
  const outputDir = path.resolve(typeof args.output_dir === "string" ? args.output_dir : process.cwd());
  const outputName = path.basename(typeof args.output_name === "string" ? args.output_name : String(requestId));
  if (result.status === "ok") {
    fs.mkdirSync(outputDir, { recursive: true });
    const choices = Array.isArray(result.choices) ? result.choices : [result];
    for (let i = 0; i < choices.length; i++) {
      const choice = choices[i];
      const name = result.choices ? `${outputName}_choice_${i+1}` : outputName;
      if (choice.cw_code) {
        const file = path.join(outputDir, `${name}.cw`);
        fs.writeFileSync(file, `# session_id: ${choice.session_id || result.session_id || ""}\n${choice.cw_code}`, "utf8");
        choice.saved_cw_file = file;
        delete choice.cw_code;
      }
      if (choice.svg) {
        const file = path.join(outputDir, `${name}.svg`);
        fs.writeFileSync(file, choice.svg, "utf8");
        choice.saved_svg_file = file;
        delete choice.svg;
      }
      Object.assign(choice, normalizeAssetResult({ ...choice, status: "ok", output_name: name, output_dir: outputDir }));
      await downloadAssetsLocally(choice);
    }
  }
  result.saved_request_record = args.record || null;
  printJson(result);
  return result;
}

module.exports = { main };
if (require.main === module) main().catch((error) => { printJson({ status: "error", error: { code: "RECEIPT_LOOKUP_FAILED", message: error.message } }); process.exitCode = 1; });
