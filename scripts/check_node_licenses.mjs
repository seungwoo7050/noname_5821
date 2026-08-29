import { readFile, readdir } from "node:fs/promises";
import path from "node:path";

const root = path.resolve("apps/web/node_modules");
const packages = [];

async function visit(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (!entry.isDirectory() || entry.name.startsWith(".")) continue;
    const child = path.join(directory, entry.name);
    if (entry.name === "node_modules" || entry.name.startsWith("@")) {
      await visit(child);
      continue;
    }
    try {
      const manifest = JSON.parse(await readFile(path.join(child, "package.json"), "utf8"));
      packages.push({ name: manifest.name ?? entry.name, license: manifest.license ?? "" });
    } catch {
      continue;
    }
    const nested = path.join(child, "node_modules");
    try {
      await visit(nested);
    } catch {
      // Most packages are flattened and have no nested dependency directory.
    }
  }
}

await visit(root);
const missing = packages.filter((item) => !item.license).map((item) => item.name).sort();
const forbidden = packages
  .filter((item) => String(item.license).toUpperCase().includes("AGPL"))
  .map((item) => item.name)
  .sort();
if (missing.length) throw new Error(`missing Node license metadata: ${missing.join(", ")}`);
if (forbidden.length) throw new Error(`forbidden Node licenses: ${forbidden.join(", ")}`);
console.log(`Node license metadata passed: ${packages.length} installed packages`);
