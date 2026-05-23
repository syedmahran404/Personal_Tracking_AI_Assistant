// Syntax-only TS parse check (no module resolution required).
import ts from "typescript";
import fs from "node:fs";
import path from "node:path";

const root = process.argv[2];
let errors = 0;
let checked = 0;

function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "node_modules" || entry.name === ".next" || entry.name === "dist") continue;
      walk(full);
    } else if (/\.(ts|tsx)$/.test(entry.name)) {
      checked++;
      const src = fs.readFileSync(full, "utf8");
      const sf = ts.createSourceFile(
        full,
        src,
        ts.ScriptTarget.ES2022,
        true,
        entry.name.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS,
      );
      const diags = sf.parseDiagnostics ?? [];
      if (diags.length > 0) {
        errors += diags.length;
        for (const d of diags) {
          const { line, character } = sf.getLineAndCharacterOfPosition(d.start ?? 0);
          const text = ts.flattenDiagnosticMessageText(d.messageText, "\n");
          console.log(`${full}:${line + 1}:${character + 1} ${text}`);
        }
      }
    }
  }
}

walk(root);
console.log(`\nChecked ${checked} files, ${errors} parse errors.`);
process.exit(errors > 0 ? 1 : 0);
