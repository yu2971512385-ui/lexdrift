# lexdrift

Syntax highlighters go stale quietly. A language ships a keyword, the grammar
in your highlighter does not get the memo, and from then on that keyword is
rendered as if it were a variable name. Nobody files a bug, because nothing
crashes -- the code just looks slightly wrong forever.

`lexdrift` measures that drift. It keeps a corpus of language features with
the version that introduced them, runs them through highlighting libraries,
and reports which features each library does not recognise.

```console
$ lexdrift check --lang go
highlightjs    11.12.0      0.0%  (0/5 recognised)
prism          1.30.0      50.0%  (3/6 recognised, 3 styled differently)
pygments       2.21.0     100.0%  (6/6 recognised)

feature               highlightjs         prism      pygments
-------------------------------------------------------------
[go]
go-any                    MISSING       MISSING            ok
go-comparable             MISSING       MISSING            ok
go-clear                  MISSING         wrong            ok
go-min                    MISSING         wrong            ok
go-max                    MISSING         wrong            ok
go-constraint-tilde         style       MISSING            ok

8 unrecognised feature(s):
  highlightjs: go predeclared type `any` since 1.18 -- highlighted as plain text
  highlightjs: go builtin `clear` since 1.21 -- highlighted as plain text
  ...
```

`any` has been Go's alias for `interface{}` since 1.18, in 2022.

## Why this is not just diffing keyword lists

Two things make the difference between a useful report and a pile of noise.

**A baseline for every feature.** Most highlight.js grammars never mark
operators, so flagging `??=` as "missing" there would be nonsense. Every
corpus entry therefore names an older construct of the same shape -- `+=` for
`??=`, `error` for `any`, `b"..."` for `c"..."`. If the library leaves the
baseline unstyled too, lexdrift reports a style choice (`◦`), not drift.

**Category over opinion.** A feature passes when the library gives it *any*
non-plain token, so the eternal "is `min` a builtin or a function call?"
argument does not produce failures. Entries may narrow that with `expect:`,
and a mismatch is then reported separately as advisory (`🟡`), never as a gap.

What counts as a gap is deliberately narrow: the feature is rendered as plain
text, or the library emits an error token on valid code.

## Install

```console
pip install lexdrift            # ready to use: the Pygments adapter is included
cd "$(python -c 'import lexdrift, pathlib; print(pathlib.Path(lexdrift.__file__).parent / "js")')"
npm install                     # optional: highlight.js and Prism adapters
```

Node is only needed for the JavaScript libraries; without it lexdrift checks
whatever is available and says why the rest was skipped.

## Use

```console
lexdrift check                            # every library, every language
lexdrift check --lib pygments --lang php  # one library, one language
lexdrift check --skip-contextual          # ignore contextual keywords
lexdrift check --format markdown > REPORT.md
lexdrift check --format json | jq '.[] | select(.library=="prism")'
lexdrift check --strict                   # exit 1 when something is missing
lexdrift list                             # what is in the corpus
lexdrift libs                             # which libraries are usable here
```

A current run of the bundled corpus lives in [REPORT.md](REPORT.md).

## What it found

The corpus that ships with 0.1.0 covers 46 features across nine languages.
Against current releases of three libraries it finds gaps such as:

| library | gap |
| --- | --- |
| Pygments | JavaScript numeric separators: `1_000_000` lexes as the number `1` followed by the identifier `_000_000` |
| Pygments | PHP 8.1 `enum` and PHP 7.4 `fn` are lexed as ordinary identifiers |
| Pygments | TypeScript 4.9 `satisfies` |
| highlight.js | Go 1.18 `any`/`comparable` and Go 1.21 `clear`/`min`/`max` |
| Prism | C# 11 raw string literals: the third quote of `"""` is left as plain text |
| all three | Rust 1.77 C string literals: `c"..."` loses its `c` prefix |

Some of these are already reported upstream (pull requests open at the time
of writing):
[PrismJS/prism#4138](https://github.com/PrismJS/prism/pull/4138),
[highlightjs/highlight.js#4553](https://github.com/highlightjs/highlight.js/pull/4553),
[ajaxorg/ace#6011](https://github.com/ajaxorg/ace/pull/6011),
[sublimehq/Packages#4620](https://github.com/sublimehq/Packages/pull/4620),
[pygments/pygments#3331](https://github.com/pygments/pygments/pull/3331).

If you send one of these upstream, please link the report line you used --
maintainers deserve a claim they can check in one command.

## Adding a feature

Corpus files are YAML, one per language, in
[`src/lexdrift/corpus/`](src/lexdrift/corpus). A feature is a snippet plus the
piece of it that carries the feature:

```yaml
- id: go-clear
  name: "builtin `clear`"
  since: "1.21"
  spec: https://go.dev/ref/spec#Clear
  snippet: |
    func reset(m map[string]int) {
    	clear(m)
    }
  token: clear
  expect: [builtin, keyword]     # optional; any non-plain category passes
  contextual: false              # true for soft keywords (`match`, `record`)
  baseline:                      # the older construct of the same shape
    snippet: |
      func size(m map[string]int) int {
      	return len(m)
      }
    token: len
```

Rules of thumb: the snippet must be valid code, the feature must be in a
released language version, and the baseline must be something the same
grammar has supported for years. Run `pytest` -- the corpus is validated by
the test suite, including that every token really occurs in its snippet.

## Adding a library

An adapter answers one question: how does this library tokenise this snippet?
Implement `version()`, `supports(language)` and `tokenize(language, code)`,
map the library's token names onto lexdrift's categories, and register it:

```python
from lexdrift.adapters import register
from lexdrift.model import Token

class MyAdapter:
    name, label, url = "mylib", "MyLib", "https://example.com/mylib"

    def version(self): ...
    def supports(self, language): ...
    def tokenize(self, language, code) -> list[Token]: ...

register(MyAdapter.name, MyAdapter)
```

`tokenize` must return every character of the input, whitespace included --
lexdrift locates features by character offset. Libraries that live in another
runtime can follow [`adapters/node.py`](src/lexdrift/adapters/node.py), which
drives a small script through a subprocess. chroma (Go), Rouge (Ruby) and Ace
are obvious next candidates.

## Limitations

- A highlighter that paints *everything* would score 100%. lexdrift measures
  recognition, not correctness.
- Contextual keywords (`match` in Python, `record` in Java) are marked as
  such, because not highlighting them is a legitimate choice; `--skip-contextual`
  drops them.
- Language identifiers are assumed to be the common ones (`go`, `csharp`,
  `cpp`); a library that names them differently needs a mapping in its adapter.

## License

MIT
