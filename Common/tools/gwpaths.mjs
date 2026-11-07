// Machine-independent paths for the workflow's Node scripts (Windows and Mac).
// Twin of gwpaths.py, same names:
//   import { ROOT, ROOT_FWD, NODE, NPX, HOME_CLAUDE, me } from "<rel>/Common/tools/gwpaths.mjs";
// ROOT = env GW_HOME, else the folder this repo is in.  ROOT_FWD = ROOT with forward slashes.
// me() = <ROOT>/_workflow/me.json {name, workflow, email}, else git global user.name/email + "My Workflow".
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

export const WIN = process.platform === "win32";
// the repo is wherever this file sits (<ROOT>/Common/tools/gwpaths.mjs), so any clone folder works
export const ROOT = process.env.GW_HOME || path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
export const ROOT_FWD = ROOT.replace(/\\/g, "/");
export const HOME_CLAUDE = path.join(os.homedir(), ".claude");
export const ME_FILE = path.join(ROOT, "_workflow", "me.json");

const which = (name) => {
  const exts = WIN ? (process.env.PATHEXT || ".EXE;.CMD;.BAT").split(";") : [""];
  for (const dir of (process.env.PATH || "").split(path.delimiter)) {
    for (const ext of exts) {
      const p = path.join(dir, name + ext.toLowerCase());
      if (dir && fs.existsSync(p)) return p;
    }
  }
  return null;
};

export const NODE = process.execPath;
const npxNext = path.join(path.dirname(process.execPath), WIN ? "npx.cmd" : "npx");
export const NPX = fs.existsSync(npxNext) ? npxNext : which("npx") || "npx";

const gitGlobal = (key) => {
  try {
    return execFileSync("git", ["config", "--global", key], { encoding: "utf8", timeout: 5000, stdio: ["ignore", "pipe", "ignore"] }).trim();
  } catch {
    return "";
  }
};

export function me() {
  let d = {};
  try {
    d = JSON.parse(fs.readFileSync(ME_FILE, "utf8"));
  } catch {}
  return {
    name: d.name || gitGlobal("user.name"),
    workflow: d.workflow || "My Workflow",
    email: d.email || gitGlobal("user.email"),
  };
}
