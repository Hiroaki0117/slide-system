#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const python = process.env.SLIDE_SYSTEM_PYTHON || (process.platform === "win32" ? "python" : "python3");
const separator = process.platform === "win32" ? ";" : ":";
const existing = process.env.PYTHONPATH || "";
const env = { ...process.env, PYTHONPATH: [path.join(root, "src"), existing].filter(Boolean).join(separator) };
const completed = spawnSync(python, ["-m", "slide_system", ...process.argv.slice(2)], { cwd: process.cwd(), env, stdio: "inherit" });
if (completed.error) {
  process.stderr.write(`slide-system: Pythonを起動できません: ${completed.error.message}\n`);
  process.exit(2);
}
process.exit(completed.status ?? 2);
