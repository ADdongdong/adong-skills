#!/usr/bin/env node
"use strict";

const fs = require("fs");
const http = require("http");
const https = require("https");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");

const PACKAGE_ID = "@user_bddf3fe6/contextweave-interactive-architecture";
const INSTALLER_URL =
  "https://skillhub-1388575217.cos.ap-guangzhou.myqcloud.com/install/latest.tar.gz";
const INSTALL_DOC_URL = "https://skillhub.cn/install/skillhub.md";
const MAX_INSTALLER_BYTES = 50 * 1024 * 1024;

function parseArgs(argv) {
  const options = {
    dryRun: false,
    skillsDir: null,
    requiredVersion: null,
    skillhubCli: null,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--dry-run") {
      options.dryRun = true;
    } else if (arg === "--skills-dir") {
      const value = argv[index + 1];
      if (!value) throw new Error("--skills-dir requires an absolute path");
      options.skillsDir = path.resolve(value);
      index += 1;
    } else if (arg === "--required-version") {
      const value = argv[index + 1];
      if (!value || !/^[0-9A-Za-z][0-9A-Za-z.+-]{0,63}$/.test(value)) {
        throw new Error("--required-version must be a simple version identifier");
      }
      options.requiredVersion = value;
      index += 1;
    } else if (arg === "--skillhub-cli") {
      const value = argv[index + 1];
      if (!value) throw new Error("--skillhub-cli requires an absolute executable or script path");
      options.skillhubCli = path.resolve(value);
      index += 1;
    } else if (arg === "--help" || arg === "-h") {
      options.help = true;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  return options;
}

function printHelp() {
  process.stdout.write(
    [
      "Update ContextWeave Interactive Architecture Skill.",
      "",
      "Usage:",
      "  node scripts/update_skill.cjs [--required-version <version>] [--skills-dir <absolute-path>]",
      "  node scripts/update_skill.cjs --dry-run",
      "",
      "The skills directory is normally inferred from this script's installed location.",
      "Use --skills-dir only for a custom or non-standard installation layout.",
      "",
    ].join("\n")
  );
}

function isPathInside(parent, child) {
  const relative = path.relative(parent, child);
  return relative && !relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative);
}

function inferLayout(overrideSkillsDir = null) {
  const scriptDir = path.resolve(__dirname);
  const skillRoot = path.dirname(scriptDir);
  const skillFile = path.join(skillRoot, "SKILL.md");
  if (!fs.existsSync(skillFile)) {
    throw new Error(`Cannot locate SKILL.md next to updater: ${skillFile}`);
  }

  const parent = path.dirname(skillRoot);
  const inferredSkillsDir = path.basename(parent).startsWith("@")
    ? path.dirname(parent)
    : parent;
  const skillsDir = path.resolve(overrideSkillsDir || inferredSkillsDir);
  if (path.parse(skillsDir).root === skillsDir) {
    throw new Error(`Refusing to use a filesystem root as skills directory: ${skillsDir}`);
  }

  const packageParts = PACKAGE_ID.split("/").filter(Boolean);
  const targetDir = path.resolve(skillsDir, ...packageParts);
  if (!isPathInside(skillsDir, targetDir)) {
    throw new Error(`Resolved install target is outside skills directory: ${targetDir}`);
  }

  return { scriptDir, skillRoot, skillsDir, targetDir };
}

function run(command, args, { inherit = true } = {}) {
  return spawnSync(command, args, {
    encoding: "utf8",
    shell: false,
    stdio: inherit ? "inherit" : "pipe",
    windowsHide: true,
  });
}

function commandWorks(command, args) {
  const result = run(command, args, { inherit: false });
  return !result.error && result.status === 0;
}

function findSkillHubCommand() {
  const candidates = process.platform === "win32"
    ? ["skillhub.cmd", "skillhub.exe", "skillhub"]
    : ["skillhub"];
  const command = candidates.find((candidate) => commandWorks(candidate, ["--version"]));
  return command ? { command, prefix: [], versionStyle: "flag", label: command } : null;
}

function findPython() {
  const candidates = process.platform === "win32"
    ? [
        { command: "py", prefix: ["-3"] },
        { command: "python3", prefix: [] },
        { command: "python", prefix: [] },
      ]
    : [
        { command: "python3", prefix: [] },
        { command: "python", prefix: [] },
      ];
  return candidates.find(({ command, prefix }) => commandWorks(command, [...prefix, "--version"])) || null;
}

function findTarCommand() {
  const candidates = process.platform === "win32" ? ["tar.exe", "tar"] : ["tar"];
  return candidates.find((candidate) => commandWorks(candidate, ["--version"])) || null;
}

function findCurlCommand() {
  const candidates = process.platform === "win32" ? ["curl.exe", "curl"] : ["curl"];
  return candidates.find((candidate) => commandWorks(candidate, ["--version"])) || null;
}

function download(url, destination, redirects = 0) {
  if (redirects > 5) return Promise.reject(new Error("Too many installer redirects"));
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const transport = parsed.protocol === "https:" ? https : http;
    const request = transport.get(parsed, { headers: { "User-Agent": "contextweave-skill-updater/1" } }, (response) => {
      if (response.statusCode >= 300 && response.statusCode < 400 && response.headers.location) {
        response.resume();
        const redirected = new URL(response.headers.location, parsed).toString();
        download(redirected, destination, redirects + 1).then(resolve, reject);
        return;
      }
      if (response.statusCode !== 200) {
        response.resume();
        reject(new Error(`Installer download failed with HTTP ${response.statusCode}`));
        return;
      }

      let received = 0;
      const output = fs.createWriteStream(destination, { flags: "wx" });
      response.on("data", (chunk) => {
        received += chunk.length;
        if (received > MAX_INSTALLER_BYTES) {
          request.destroy(new Error("Installer archive exceeds 50 MB safety limit"));
        }
      });
      response.pipe(output);
      output.on("finish", () => output.close(resolve));
      output.on("error", reject);
    });
    request.setTimeout(30000, () => request.destroy(new Error("Installer download timed out")));
    request.on("error", reject);
  });
}

async function downloadInstaller(destination) {
  const curlCommand = findCurlCommand();
  if (curlCommand) {
    const result = run(
      curlCommand,
      [
        "--fail",
        "--location",
        "--silent",
        "--show-error",
        "--max-time",
        "30",
        "--max-filesize",
        String(MAX_INSTALLER_BYTES),
        "--output",
        destination,
        INSTALLER_URL,
      ],
      { inherit: false }
    );
    if (!result.error && result.status === 0) return;
    fs.rmSync(destination, { force: true });
    const reason = String(result.stderr || result.error?.message || "unknown error").trim();
    process.stderr.write(`curl download failed (${reason}); falling back to Node HTTPS.\n`);
  }
  await download(INSTALLER_URL, destination);
}

function readSkillVersion(skillFile) {
  if (!fs.existsSync(skillFile)) return null;
  const content = fs.readFileSync(skillFile, "utf8");
  const match = content.match(/^version:\s*["']?([^\s"']+)/m);
  return match ? match[1] : null;
}

function resolveExplicitSkillHub(cliPath) {
  if (!path.isAbsolute(cliPath) || !fs.existsSync(cliPath)) {
    throw new Error(`Custom SkillHub CLI was not found: ${cliPath}`);
  }
  const extension = path.extname(cliPath).toLowerCase();
  if (extension === ".js" || extension === ".cjs" || extension === ".mjs") {
    return {
      command: process.execPath,
      prefix: [cliPath],
      versionStyle: "flag",
      label: cliPath,
    };
  }
  if (extension === ".py") {
    const python = findPython();
    if (!python) throw new Error("Python 3 is required to run the custom SkillHub CLI script");
    return {
      command: python.command,
      prefix: [...python.prefix, cliPath],
      versionStyle: "ref",
      label: cliPath,
    };
  }
  return { command: cliPath, prefix: [], versionStyle: "flag", label: cliPath };
}

function installArgs(prefixArgs, skillsDir, requiredVersion, versionStyle) {
  const packageRef = requiredVersion && versionStyle === "ref"
    ? `${PACKAGE_ID}@${requiredVersion}`
    : PACKAGE_ID;
  const args = [
    ...prefixArgs,
    "install",
    packageRef,
    "--dir",
    skillsDir,
    "--force",
  ];
  if (requiredVersion && versionStyle === "flag") {
    args.push("--version", requiredVersion);
  }
  return args;
}

function runInstall(cli, skillsDir, requiredVersion = null) {
  let result = run(
    cli.command,
    installArgs(cli.prefix, skillsDir, requiredVersion, cli.versionStyle)
  );
  if (
    requiredVersion &&
    cli.versionStyle === "flag" &&
    (result.error || result.status !== 0)
  ) {
    process.stderr.write("SkillHub --version install failed; retrying with a versioned package reference.\n");
    result = run(
      cli.command,
      installArgs(cli.prefix, skillsDir, requiredVersion, "ref")
    );
  }
  return !result.error && result.status === 0;
}

async function installWithBundledCli(skillsDir, requiredVersion) {
  const tarCommand = findTarCommand();
  if (!tarCommand) throw new Error("tar is required to unpack the SkillHub installer");
  const python = findPython();
  if (!python) {
    throw new Error(`Python 3 was not found. Install SkillHub using ${INSTALL_DOC_URL}, then rerun this updater.`);
  }

  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "contextweave-skill-update-"));
  const archivePath = path.join(tempDir, "latest.tar.gz");
  try {
    process.stderr.write("Downloading the official SkillHub installer...\n");
    await downloadInstaller(archivePath);
    const extracted = run(tarCommand, ["-xzf", archivePath, "-C", tempDir]);
    if (extracted.error || extracted.status !== 0) {
      throw new Error("Failed to extract the SkillHub installer archive");
    }

    const cliCandidates = [
      path.join(tempDir, "cli", "skills_store_cli.py"),
      path.join(tempDir, "skills_store_cli.py"),
    ];
    const cliPath = cliCandidates.find((candidate) => fs.existsSync(candidate));
    if (!cliPath) throw new Error("The SkillHub installer archive does not contain skills_store_cli.py");

    const bundledCli = {
      command: python.command,
      prefix: [...python.prefix, cliPath],
      versionStyle: "ref",
      label: cliPath,
    };
    if (!runInstall(bundledCli, skillsDir, requiredVersion)) {
      throw new Error("SkillHub installer failed to update the ContextWeave Skill");
    }
  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    printHelp();
    return;
  }

  const layout = inferLayout(options.skillsDir);
  const dryRunPayload = {
    status: "ok",
    dry_run: true,
    package_id: PACKAGE_ID,
    skill_root: layout.skillRoot,
    skills_dir: layout.skillsDir,
    target_dir: layout.targetDir,
    required_version: options.requiredVersion,
    installer_url: INSTALLER_URL,
  };
  if (options.dryRun) {
    process.stdout.write(`${JSON.stringify(dryRunPayload)}\n`);
    return;
  }

  process.stdout.write("==========================================\n");
  process.stdout.write("Updating ContextWeave Interactive Architecture Skill\n");
  process.stdout.write("==========================================\n");
  process.stdout.write(`Skills directory: ${layout.skillsDir}\n`);

  const skillhub = options.skillhubCli
    ? resolveExplicitSkillHub(options.skillhubCli)
    : findSkillHubCommand();
  let installed = false;
  if (skillhub) {
    process.stderr.write(`Using SkillHub CLI: ${skillhub.label}\n`);
    installed = runInstall(skillhub, layout.skillsDir, options.requiredVersion);
    if (!installed) {
      process.stderr.write("Installed SkillHub CLI failed; retrying with the official temporary installer.\n");
    }
  }
  if (!installed) {
    await installWithBundledCli(layout.skillsDir, options.requiredVersion);
  }

  const installedSkillFile = path.join(layout.targetDir, "SKILL.md");
  const installedVersion = readSkillVersion(installedSkillFile);
  if (!installedVersion) {
    throw new Error(
      `Update command completed, but the installed SKILL.md was not found at ${installedSkillFile}`
    );
  }
  if (options.requiredVersion && installedVersion !== options.requiredVersion) {
    throw new Error(
      `Installed version ${installedVersion} does not match required version ${options.requiredVersion}`
    );
  }

  process.stdout.write("==========================================\n");
  process.stdout.write(`Update completed successfully. Installed version: ${installedVersion}\n`);
  process.stdout.write("Start a new Skill script process and retry the original request once.\n");
}

main().catch((error) => {
  process.stderr.write(`ContextWeave Skill update failed: ${error.message || error}\n`);
  process.stderr.write(`Manual installation guide: ${INSTALL_DOC_URL}\n`);
  process.exitCode = 1;
});
