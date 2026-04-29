#!/usr/bin/env node

const fs = require("fs");
const os = require("os");
const path = require("path");
const childProcess = require("child_process");

const marker = "var admonitionStyle = {";

function run(command, args) {
  try {
    return childProcess.execFileSync(command, args, {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
  } catch {
    return "";
  }
}

function existing(file) {
  return file && fs.existsSync(file) ? path.resolve(file) : "";
}

function collectCandidates() {
  const candidates = new Set();
  if (process.env.MYST_CJS_PATH) candidates.add(process.env.MYST_CJS_PATH);

  const pyPath = run("python", [
    "-c",
    "import pathlib, mystmd_py; print(pathlib.Path(mystmd_py.__file__).with_name('myst.cjs'))",
  ]);
  if (pyPath) candidates.add(pyPath);

  const npmRoot = run("npm", ["root", "-g"]);
  if (npmRoot) {
    candidates.add(path.join(npmRoot, "mystmd"));
    candidates.add(path.join(npmRoot, "mystmd", "dist", "myst.cjs"));
    candidates.add(path.join(npmRoot, "mystmd", "myst.cjs"));
  }

  let mystBin = "";
  const pathExt = process.platform === "win32" ? [".exe", ".cmd", ".ps1", ""] : [""];
  for (const dir of (process.env.PATH || "").split(path.delimiter)) {
    for (const ext of pathExt) {
      const candidate = path.join(dir, `myst${ext}`);
      if (fs.existsSync(candidate)) {
        mystBin = candidate;
        break;
      }
    }
    if (mystBin) break;
  }
  if (!mystBin) {
    const command = process.platform === "win32" ? "where.exe" : "which";
    mystBin = run(command, ["myst"]).split(/\r?\n/).find(Boolean);
  }
  if (mystBin) {
    candidates.add(mystBin);
    candidates.add(path.resolve(path.dirname(mystBin), "..", "lib", "node_modules", "mystmd", "dist", "myst.cjs"));
    candidates.add(path.resolve(path.dirname(mystBin), "..", "Lib", "site-packages", "mystmd_py", "myst.cjs"));
    candidates.add(path.resolve(path.dirname(mystBin), "..", "lib", "python3.12", "site-packages", "mystmd_py", "myst.cjs"));
  }

  return [...candidates].map(existing).filter(Boolean);
}

function findBundle() {
  const queue = collectCandidates();
  const seen = new Set();

  while (queue.length) {
    const current = queue.shift();
    if (!current || seen.has(current)) continue;
    seen.add(current);

    let stat;
    try {
      stat = fs.statSync(current);
    } catch {
      continue;
    }

    if (stat.isFile()) {
      if (current.endsWith(".cjs") || current.endsWith(".js")) {
        const text = fs.readFileSync(current, "utf8");
        if (text.includes(marker)) return current;
      }
      continue;
    }

    if (!stat.isDirectory()) continue;
    for (const entry of fs.readdirSync(current)) {
      if (entry === "node_modules" || entry === ".git") continue;
      const next = path.join(current, entry);
      if (entry === "myst.cjs" || entry.endsWith(".js") || fs.statSync(next).isDirectory()) {
        queue.push(next);
      }
    }
  }

  throw new Error("Could not find the MyST DOCX renderer bundle. Set MYST_CJS_PATH to myst.cjs.");
}

function replaceOnce(source, from, to, label) {
  if (source.includes(to)) return source;
  if (!source.includes(from)) {
    throw new Error(`Could not find patch target: ${label}`);
  }
  return source.replace(from, to);
}

const bundle = findBundle();
let source = fs.readFileSync(bundle, "utf8");
const original = source;

source = replaceOnce(
  source,
  `function basicIndentStyle(indent2) {
  return {
    alignment: import_docx2.AlignmentType.START,
    style: {
      paragraph: {
        indent: { left: (0, import_docx2.convertInchesToTwip)(indent2), hanging: (0, import_docx2.convertInchesToTwip)(0.18) }
      }
    }
  };
}
var numbered = Array(3).fill([import_docx2.LevelFormat.DECIMAL, import_docx2.LevelFormat.LOWER_LETTER, import_docx2.LevelFormat.LOWER_ROMAN]).flat().map((format, level) => ({
  level,
  format,
  text: \`%\${level + 1}.\`,
  ...basicIndentStyle((level + 1) / 2)
}));
var bullets = Array(3).fill(["\\u25CF", "\\u25CB", "\\u25A0"]).flat().map((text7, level) => ({
  level,
  format: import_docx2.LevelFormat.BULLET,
  text: text7,
  ...basicIndentStyle((level + 1) / 2)
}));`,
  `function basicIndentStyle(indent2) {
  return {
    alignment: import_docx2.AlignmentType.START,
    style: {
      paragraph: {
        indent: { left: (0, import_docx2.convertInchesToTwip)(indent2), hanging: (0, import_docx2.convertInchesToTwip)(0.14) }
      }
    }
  };
}
var numbered = Array(3).fill([import_docx2.LevelFormat.DECIMAL, import_docx2.LevelFormat.LOWER_LETTER, import_docx2.LevelFormat.LOWER_ROMAN]).flat().map((format, level) => ({
  level,
  format,
  text: \`%\${level + 1}.\`,
  ...basicIndentStyle(0.36 * (level + 1))
}));
var bullets = Array(3).fill(["\\u2022", "\\u2013", "\\u25E6"]).flat().map((text7, level) => ({
  level,
  format: import_docx2.LevelFormat.BULLET,
  text: text7,
  style: {
    paragraph: {
      indent: { left: (0, import_docx2.convertInchesToTwip)(0.34 * (level + 1)), hanging: (0, import_docx2.convertInchesToTwip)(0.14) }
    },
    run: { color: "5F666D", size: 18 }
  }
}));`,
  "list numbering styles",
);

source = replaceOnce(
  source,
  `var admonitionStyle = {
  border: {
    left: {
      style: import_docx3.BorderStyle.DOUBLE,
      color: "5D85D0"
    }
  },
  indent: { left: (0, import_docx3.convertInchesToTwip)(0.2), right: (0, import_docx3.convertInchesToTwip)(0.2) }
};
var admonition3 = (state, node3) => {
  state.blankLine();
  state.renderChildren(node3, admonitionStyle);
  state.closeBlock();
  state.blankLine();
};
var admonitionTitle2 = (state, node3) => {
  state.renderChildren(node3, {
    ...admonitionStyle,
    shading: {
      type: import_docx3.ShadingType.SOLID,
      color: "5D85D0"
    }
  }, { bold: true, color: "FFFFFF" });
  state.closeBlock();
};`,
  `var admonitionStyle = {
  border: {
    left: {
      style: import_docx3.BorderStyle.SINGLE,
      color: "AEB8C2",
      size: 8,
      space: 10
    }
  },
  indent: { left: (0, import_docx3.convertInchesToTwip)(0.28), right: (0, import_docx3.convertInchesToTwip)(0.18) },
  spacing: { before: 120, after: 120, line: 280 }
};
var admonition3 = (state, node3) => {
  state.blankLine();
  state.renderChildren(node3, admonitionStyle);
  state.closeBlock();
  state.blankLine();
};
var admonitionTitle2 = (state, node3) => {
  state.renderChildren(node3, {
    ...admonitionStyle,
    shading: {
      type: import_docx3.ShadingType.SOLID,
      color: "EEF2F5"
    },
    spacing: { before: 120, after: 40, line: 260 }
  }, { bold: true, color: "2F3A42" });
  state.closeBlock();
};`,
  "admonition styles",
);

source = replaceOnce(
  source,
  `        children: state.children,
        footers: footer2 ? { default: footer2 } : void 0`,
  `        children: state.options.addTableOfContents === false ? state.children : [
          new import_docx.Paragraph({
            children: [new import_docx.TextRun({ text: "Sommaire", bold: true, size: 30, color: "2B3033" })],
            spacing: { before: 360, after: 180 }
          }),
          new import_docx.TableOfContents("Sommaire", {
            hyperlink: true,
            headingStyleRange: "1-3",
            hideTabAndPageNumbersInWebView: true,
            useAppliedParagraphOutlineLevel: true
          }),
          new import_docx.Paragraph({ children: [new import_docx.PageBreak()] }),
          ...state.children
        ],
        footers: footer2 ? { default: footer2 } : void 0`,
  "automatic table of contents",
);

if (source !== original) {
  const backup = `${bundle}.pre-docx-style-patch`;
  if (!fs.existsSync(backup)) fs.copyFileSync(bundle, backup);
  fs.writeFileSync(bundle, source);
  console.log(`Patched MyST DOCX renderer: ${bundle}`);
} else {
  console.log(`MyST DOCX renderer already patched: ${bundle}`);
}

console.log(`Platform: ${os.platform()} ${os.release()}`);
