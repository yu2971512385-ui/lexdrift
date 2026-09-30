// Tokenise snippets with a JavaScript highlighting library.
//
// Protocol: one JSON request on stdin, one JSON response on stdout.
//   in : {"library": "highlightjs"|"prism", "requests": [{"language": "go", "code": "..."}]}
//   out: {"version": "11.12.0", "results": [[{"text": "var", "raw": "keyword"}, ...]]}
// Errors are reported as {"error": "..."} with a non-zero exit code.

import process from "node:process";

function readStdin() {
  return new Promise((resolve, reject) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
    process.stdin.on("error", reject);
  });
}

const HTML_ENTITIES = {
  "&amp;": "&",
  "&lt;": "<",
  "&gt;": ">",
  "&quot;": '"',
  "&#x27;": "'",
  "&#39;": "'",
};

function decodeEntities(text) {
  return text.replace(/&(?:amp|lt|gt|quot|#x27|#39);/g, (match) => HTML_ENTITIES[match]);
}

// highlight.js emits nested <span class="hljs-*"> markup. Walking it with a
// stack gives us the innermost class for every piece of text, which is the
// one that decides how the token is displayed.
function tokensFromHljsHtml(html) {
  const tokens = [];
  const stack = [];
  const pattern = /<span class="([^"]*)">|<\/span>/g;
  let index = 0;
  let match;

  const push = (text) => {
    if (!text) return;
    const cls = stack.length ? stack[stack.length - 1] : "";
    tokens.push({ text: decodeEntities(text), raw: cls });
  };

  while ((match = pattern.exec(html)) !== null) {
    push(html.slice(index, match.index));
    if (match[0] === "</span>") {
      stack.pop();
    } else {
      const classes = match[1]
        .split(/\s+/)
        .filter(Boolean)
        .map((name) => name.replace(/^hljs-/, ""));
      stack.push(classes.join("."));
    }
    index = pattern.lastIndex;
  }
  push(html.slice(index));
  return tokens;
}

async function runHighlightJs(requests) {
  const module = await import("highlight.js");
  const hljs = module.default ?? module;
  const results = requests.map(({ language, code }) => {
    if (!hljs.getLanguage(language)) return null;
    const { value } = hljs.highlight(code, { language, ignoreIllegals: true });
    return tokensFromHljsHtml(value);
  });
  return { version: hljs.versionString ?? "", results };
}

function flattenPrism(token, inherited, out) {
  if (typeof token === "string") {
    out.push({ text: token, raw: inherited });
    return;
  }
  const type = token.type || inherited;
  const content = token.content;
  if (Array.isArray(content)) {
    for (const child of content) flattenPrism(child, type, out);
  } else if (typeof content === "string") {
    out.push({ text: content, raw: type });
  } else if (content) {
    flattenPrism(content, type, out);
  }
}

async function runPrism(requests) {
  const module = await import("prismjs");
  const Prism = module.default ?? module;
  const loader = await import("prismjs/components/index.js");
  const loadLanguages = loader.default ?? loader;
  loadLanguages.silent = true;

  const results = requests.map(({ language, code }) => {
    if (!Prism.languages[language]) {
      try {
        loadLanguages([language]);
      } catch {
        return null;
      }
    }
    const grammar = Prism.languages[language];
    if (!grammar) return null;
    const out = [];
    for (const token of Prism.tokenize(code, grammar)) flattenPrism(token, "", out);
    return out;
  });
  let version = "";
  try {
    const meta = await import("prismjs/package.json", { with: { type: "json" } });
    version = (meta.default ?? meta).version ?? "";
  } catch {
    version = "";
  }
  return { version, results };
}

async function main() {
  const payload = JSON.parse(await readStdin());
  const requests = payload.requests ?? [];
  let response;
  switch (payload.library) {
    case "highlightjs":
      response = await runHighlightJs(requests);
      break;
    case "prism":
      response = await runPrism(requests);
      break;
    default:
      throw new Error(`unknown library: ${payload.library}`);
  }
  process.stdout.write(JSON.stringify(response));
}

main().catch((error) => {
  process.stdout.write(JSON.stringify({ error: String(error && error.message ? error.message : error) }));
  process.exitCode = 1;
});
