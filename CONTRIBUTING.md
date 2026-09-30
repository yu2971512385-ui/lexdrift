# Contributing

Two kinds of contribution are especially welcome: **a feature the corpus is
missing**, and **an adapter for a library lexdrift cannot drive yet**.

## Setup

```console
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest -q

cd src/lexdrift/js && npm install   # optional: highlight.js and Prism
```

## Adding a language feature

Corpus files live in `src/lexdrift/corpus/`, one YAML file per language. See
the README for the field reference. Before opening a pull request:

- The snippet must be **valid code** for the language, and small.
- `since` must be a **released** version, and `spec` should point at the
  language reference or release note that introduced the feature -- that link
  is what makes a report actionable for a maintainer downstream.
- Add a `baseline` unless the feature has no older equivalent. Without it,
  libraries that never style that kind of token get blamed unfairly.
- Mark soft/contextual keywords with `contextual: true`.
- `pytest -q` validates every entry.

Please do not add a feature purely to make a library look bad: an entry whose
baseline is also unstyled everywhere tells nobody anything.

## Adding a library adapter

Start from `src/lexdrift/adapters/pygments_adapter.py` (in-process) or
`src/lexdrift/adapters/node.py` (another runtime through a subprocess). An
adapter must:

- return **every character** of the input from `tokenize`, whitespace
  included, so features can be located by offset;
- map the library's own token names onto lexdrift's categories, mapping
  "this is just an identifier" to `plain` -- that mapping is the heart of the
  adapter, and getting it wrong produces false reports;
- raise `AdapterUnavailable` (never crash) when the library or its runtime is
  not installed.

Add a couple of tests: the category mapping, and a round trip asserting that
the reassembled token text equals the input.

## Reporting gaps upstream

If lexdrift finds something and you take it to the library's own tracker,
include the snippet, the version you tested, and what the token came out as.
Maintainers are not obliged to agree with the corpus -- if they consider a
case a style choice, send a pull request here that turns the entry into a
`baseline` or marks it `contextual`.
