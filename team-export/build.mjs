// Exports the Features and Team sections into the team repository (dexterialk/ATP_cs-06),
// in the layout the team agreed on:
//   landing-page-components/components/features.html, team.html
//   landing-page-components/css/features.css, team.css
//   landing-page-components/js/features.js
//   landing-page-components/images/features/ (film frames), images/team/ (portraits)
//
// The React components in web/components/ stay the source. This script turns them into plain
// files with readable class names (dx-feat-..., dx-team-...) so they cannot clash with other sections.
//
// Run from the project root:  node team-export/build.mjs
import { build } from "../integration-test/team-vite-app/node_modules/esbuild/lib/main.js";
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const ROOT = process.cwd();
const OUT = path.join(ROOT, "team-repo/landing-page-components");
const NODE_MODULES = path.join(ROOT, "web/demo/node_modules");
const SECTIONS = {
  features: { dir: "web/components/features-v4", css: "FeaturesSection.module.css", prefix: "dx-feat-" },
  team: { dir: "web/components/team-v4", css: "TeamSection.module.css", prefix: "dx-team-" },
};

// CSS Modules -> plain CSS with prefixed class and animation names
function prefixCss(css, prefix) {
  const keyframes = [...css.matchAll(/@keyframes\s+([\w-]+)/g)].map((m) => m[1]);
  for (const k of keyframes) {
    css = css.replace(new RegExp(`(?<![.\\w-])${k}(?![\\w-])`, "g"), prefix + k);
  }
  return css.replace(/(?<![\w-])\.([a-zA-Z_][\w-]*)/g, (m, name) =>
    name.startsWith(prefix) ? m : "." + prefix + name
  );
}

// In the JS, styles.foo becomes "dx-feat-foo" (matches the CSS above)
const classNames = {
  name: "class-names",
  setup(b) {
    b.onResolve({ filter: /\.module\.css$/ }, (a) => ({ path: path.resolve(a.resolveDir, a.path), namespace: "cls" }));
    b.onLoad({ filter: /.*/, namespace: "cls" }, (a) => {
      const prefix = a.path.includes("team-") ? SECTIONS.team.prefix : SECTIONS.features.prefix;
      return { contents: `export default new Proxy({}, { get: (_, k) => typeof k === "string" ? "${prefix}" + k : undefined });`, loader: "js" };
    });
  },
};

const common = {
  bundle: true, write: false, jsx: "automatic", loader: { ".js": "jsx" }, logLevel: "error",
  nodePaths: [NODE_MODULES], plugins: [classNames],
};

for (const d of ["components", "css", "js", "images/features", "images/team"]) fs.mkdirSync(path.join(OUT, d), { recursive: true });

// 1. CSS
for (const [name, s] of Object.entries(SECTIONS)) {
  const css = fs.readFileSync(path.join(ROOT, s.dir, s.css), "utf8");
  fs.writeFileSync(path.join(OUT, "css", `${name}.css`), prefixCss(css, s.prefix));
}

// 2. Features: one script. Reads the frames folder from data-frames on the mount point.
//    The anchor data is included so the page also works when opened straight from a folder.
const anchors = fs.readFileSync(path.join(ROOT, "web/demo/public/dexteria/v51/anchors.json"), "utf8");
const featuresEntry = `
import { createRoot } from "react-dom/client";
import FeaturesSection from "./${SECTIONS.features.dir}/FeaturesSection";
const ANCHORS = ${anchors.trim()};
const realFetch = window.fetch.bind(window);
window.fetch = (u, o) => String(u).endsWith("anchors.json")
  ? Promise.resolve(new Response(JSON.stringify(ANCHORS), { headers: { "Content-Type": "application/json" } }))
  : realFetch(u, o);
const el = document.getElementById("dx-features");
createRoot(el).render(<FeaturesSection framesPath={el.dataset.frames || "../images/features"} />);
`;
const js = await build({
  ...common, stdin: { contents: featuresEntry, resolveDir: ROOT, loader: "jsx" },
  format: "iife", minify: true, define: { "process.env.NODE_ENV": '"production"' },
  target: ["chrome90", "safari14", "firefox90", "edge90"],
});
fs.writeFileSync(path.join(OUT, "js/features.js"),
  "/* Dexteria Features section (built from the React source in ZainaZayan/Dexteria-featuresandteam). */\n" + js.outputFiles[0].text);

// 3. Team: no JavaScript needed, so render it once to plain HTML.
const teamEntry = `
import { renderToStaticMarkup } from "react-dom/server";
import TeamSection from "./${SECTIONS.team.dir}/TeamSection";
module.exports = renderToStaticMarkup(<TeamSection photosPath="../images/team" />);
`;
const tmp = path.join(ROOT, "team-export/.team-render.cjs");
const t = await build({ ...common, stdin: { contents: teamEntry, resolveDir: ROOT, loader: "jsx" }, format: "cjs", platform: "node", define: { "process.env.NODE_ENV": '"production"' } });
fs.writeFileSync(tmp, t.outputFiles[0].text);
const { default: teamHtml } = await import(pathToFileURL(tmp).href);
fs.rmSync(tmp);

// 4. Pages
const head = (title, css) => `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dexteria – ${title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../css/${css}">
<style>body{margin:0;background:#F0ECE3}</style>
</head>
<body>
`;
fs.writeFileSync(path.join(OUT, "components/features.html"), head("Features", "features.css") +
`
<!-- FEATURES: the scroll film is drawn into this div by js/features.js.
     data-frames is the folder with the film frames, relative to this page. -->
<div id="dx-features" data-frames="../images/features"></div>

<script src="../js/features.js"></script>
</body>
</html>
`);
fs.writeFileSync(path.join(OUT, "components/team.html"), head("Team", "team.css") +
`
<!-- TEAM -->
${teamHtml.replace(/></g, ">\n<")}

</body>
</html>
`);

// 5. Images
fs.cpSync(path.join(ROOT, "web/demo/public/dexteria/v51/d"), path.join(OUT, "images/features/d"), { recursive: true });
fs.cpSync(path.join(ROOT, "web/demo/public/dexteria/v51/m"), path.join(OUT, "images/features/m"), { recursive: true });
for (const f of fs.readdirSync(path.join(ROOT, "web/demo/public/team"))) {
  if (f.endsWith(".webp") && f !== "placeholder.webp") fs.copyFileSync(path.join(ROOT, "web/demo/public/team", f), path.join(OUT, "images/team", f));
}
console.log("done");
