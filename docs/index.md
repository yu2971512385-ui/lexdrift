---
layout: default
title: lexdrift
description: How far behind the languages are the syntax highlighters?
---

# lexdrift

Syntax highlighters go stale quietly: a language ships a keyword, the grammar
does not get the memo, and from then on that keyword renders as if it were a
variable name. This page is regenerated every week by
[the report workflow](https://github.com/yu2971512385-ui/lexdrift/actions/workflows/report.yml) and says how far
behind each library currently is.

A feature counts as **missing** only when the library renders it as plain
text, or emits an error token on valid code. When a library styles no token
of that kind at all -- most highlight.js grammars never mark operators, for
instance -- the corpus entry's baseline catches it and the cell shows `◦`
instead, because that is a style choice rather than drift.

Source, corpus and the tool itself: [https://github.com/yu2971512385-ui/lexdrift](https://github.com/yu2971512385-ui/lexdrift).

_Last regenerated: 2026-09-30 08:37 UTC._

| library | version | coverage | gaps |
| --- | --- | --- | --- |
| [ace](https://github.com/ajaxorg/ace) | `1.44.0` | 42% (18/43) | 25 |
| [chroma](https://github.com/alecthomas/chroma) | `v2.14.0` | 60% (27/45) | 18 |
| [highlightjs](https://github.com/highlightjs/highlight.js) | `11.12.0` | 80% (32/40) | 8 |
| [prism](https://github.com/PrismJS/prism) | `1.30.0` | 76% (34/45) | 11 |
| [pygments](https://github.com/pygments/pygments) | `2.21.0` | 80% (35/44) | 9 |

✅ recognised · ❌ plain text · 🟡 unexpected category · 🛑 error token · ◦ library does not style this kind of token · · not locatable · – no grammar


## cpp

| feature | since | ace | chroma | highlightjs | prism | pygments |
| --- | --- | --- | --- | --- | --- | --- |
| [`concept` definition](https://en.cppreference.com/w/cpp/language/constraints) | C++20 | ❌ | ✅ | ✅ | ✅ | ✅ |
| [`requires` expression](https://en.cppreference.com/w/cpp/language/requires) | C++20 | ❌ | ✅ | ✅ | ✅ | ✅ |
| [`consteval` function](https://en.cppreference.com/w/cpp/language/consteval) | C++20 | ❌ | ✅ | ✅ | ✅ | ✅ |
| [`constinit` variable](https://en.cppreference.com/w/cpp/language/constinit) | C++20 | ❌ | ❌ | ✅ | ✅ | ✅ |
| [`co_await` expression](https://en.cppreference.com/w/cpp/language/coroutines) | C++20 | ❌ | ✅ | ✅ | ✅ | ✅ |
| [`module` declaration](https://en.cppreference.com/w/cpp/language/modules) | C++20 | ❌ | ❌ | ✅ | ✅ | ✅ |

## csharp

| feature | since | ace | chroma | highlightjs | prism | pygments |
| --- | --- | --- | --- | --- | --- | --- |
| [`record` type](https://learn.microsoft.com/dotnet/csharp/language-reference/builtin-types/record) | 9.0 | ❌ | ✅ | ✅ | ✅ | ✅ |
| [`init` accessor](https://learn.microsoft.com/dotnet/csharp/language-reference/keywords/init) | 9.0 | ❌ | ✅ | ✅ | ✅ | ✅ |
| [`required` member](https://learn.microsoft.com/dotnet/csharp/language-reference/keywords/required) | 11.0 | ❌ | ❌ | ✅ | ❌ | ❌ |
| [`file` access modifier](https://learn.microsoft.com/dotnet/csharp/language-reference/keywords/file) | 11.0 | ❌ | ❌ | ✅ | ❌ | ✅ |
| [raw string literal `"""`](https://learn.microsoft.com/dotnet/csharp/language-reference/tokens/raw-string) | 11.0 | ✅ | ✅ | ✅ | ❌ | ✅ |

## go

| feature | since | ace | chroma | highlightjs | prism | pygments |
| --- | --- | --- | --- | --- | --- | --- |
| [predeclared type `any`](https://go.dev/ref/spec#Predeclared_identifiers) | 1.18 | ❌ | ❌ | ❌ | ❌ | ✅ |
| [predeclared type `comparable`](https://go.dev/ref/spec#Predeclared_identifiers) | 1.18 | ❌ | ❌ | ❌ | ❌ | ✅ |
| [builtin `clear`](https://go.dev/ref/spec#Clear) | 1.21 | ✅ | ✅ | ❌ | 🟡 | ✅ |
| [builtin `min`](https://go.dev/ref/spec#Min_and_max) | 1.21 | ✅ | ✅ | ❌ | 🟡 | ✅ |
| [builtin `max`](https://go.dev/ref/spec#Min_and_max) | 1.21 | ✅ | ✅ | ❌ | 🟡 | ✅ |
| [`~T` in a type constraint](https://go.dev/ref/spec#General_interfaces) | 1.18 | ✅ | ✅ | ◦ | ❌ | ✅ |

## java

| feature | since | ace | chroma | highlightjs | prism | pygments |
| --- | --- | --- | --- | --- | --- | --- |
| [`sealed` class](https://openjdk.org/jeps/409) | 17 | ✅ | ✅ | ✅ | ✅ | ✅ |
| [`permits` clause](https://openjdk.org/jeps/409) | 17 | ✅ | ❌ | ✅ | ✅ | ✅ |
| [`record` declaration](https://openjdk.org/jeps/395) | 16 | ✅ | ✅ | ✅ | ✅ | ✅ |
| [text block `"""`](https://openjdk.org/jeps/378) | 15 | ✅ | ✅ | ✅ | ✅ | ✅ |

## javascript

| feature | since | ace | chroma | highlightjs | prism | pygments |
| --- | --- | --- | --- | --- | --- | --- |
| [private class field `#x`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Classes/Private_properties) | ES2022 | ◦ | 🛑 | ◦ | ◦ | ◦ |
| [logical assignment `??=`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing_assignment) | ES2021 | ✅ | ✅ | ◦ | ✅ | ✅ |
| [numeric separator `1_000_000`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Lexical_grammar#numeric_separators) | ES2021 | ✅ | ✅ | ✅ | ✅ | ❌ |
| [BigInt literal `9007199254740993n`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/BigInt) | ES2020 | ❌ | ❌ | ✅ | ✅ | ✅ |
| [optional chaining `?.`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Operators/Optional_chaining) | ES2020 | 🟡 | ✅ | ◦ | ✅ | ✅ |

## php

| feature | since | ace | chroma | highlightjs | prism | pygments |
| --- | --- | --- | --- | --- | --- | --- |
| [`enum` declaration](https://www.php.net/manual/en/language.enumerations.php) | 8.1 | ❌ | ❌ | ✅ | ✅ | ❌ |
| [`readonly` property](https://www.php.net/manual/en/language.oop5.properties.php#language.oop5.properties.readonly-properties) | 8.1 | ❌ | ❌ | ✅ | ✅ | ✅ |
| [`never` return type](https://www.php.net/manual/en/language.types.never.php) | 8.1 | ◦ | ◦ | 🟡 | ✅ | ◦ |
| [nullsafe operator `?->`](https://www.php.net/manual/en/language.oop5.basic.php#language.oop5.basic.nullsafe) | 8.0 | ❌ | ✅ | ◦ | ✅ | ✅ |
| [`match` expression](https://www.php.net/manual/en/control-structures.match.php) | 8.0 | ❌ | ❌ | ✅ | ✅ | ✅ |
| [arrow function `fn`](https://www.php.net/manual/en/functions.arrow.php) | 7.4 | ❌ | ❌ | ✅ | ✅ | ❌ |

## python

| feature | since | ace | chroma | highlightjs | prism | pygments |
| --- | --- | --- | --- | --- | --- | --- |
| [`match` statement](https://peps.python.org/pep-0634/) | 3.10 | ❌ | ✅ | ✅ | ✅ | ✅ |
| [`case` clause](https://peps.python.org/pep-0634/) | 3.10 | ❌ | ✅ | ✅ | ✅ | ✅ |
| [`type` alias statement](https://peps.python.org/pep-0695/) | 3.12 | ✅ | ✅ | ✅ | ✅ | ✅ |
| [assignment expression `:=`](https://peps.python.org/pep-0572/) | 3.8 | ✅ | ✅ | ◦ | ✅ | ✅ |

## rust

| feature | since | ace | chroma | highlightjs | prism | pygments |
| --- | --- | --- | --- | --- | --- | --- |
| [`dyn Trait`](https://doc.rust-lang.org/reference/types/trait-object.html) | 1.27 | ✅ | ✅ | ✅ | ✅ | ✅ |
| [`async fn`](https://doc.rust-lang.org/reference/items/functions.html#async-functions) | 1.39 | ✅ | ✅ | ✅ | ✅ | ✅ |
| [postfix `.await`](https://doc.rust-lang.org/reference/expressions/await-expr.html) | 1.39 | ✅ | ✅ | ✅ | ✅ | ✅ |
| [C string literal `c"..."`](https://doc.rust-lang.org/reference/tokens.html#c-string-literals) | 1.77 | ◦ | ❌ | ❌ | ❌ | ❌ |
| [raw string literal `r#"..."#`](https://doc.rust-lang.org/reference/tokens.html#raw-string-literals) | 1.0 | ✅ | ✅ | ✅ | ✅ | ✅ |

## typescript

| feature | since | ace | chroma | highlightjs | prism | pygments |
| --- | --- | --- | --- | --- | --- | --- |
| [`satisfies` operator](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html) | 4.9 | ❌ | 🛑 | ✅ | ❌ | ❌ |
| [`accessor` auto-accessor](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html) | 4.9 | ❌ | ❌ | ❌ | ❌ | ❌ |
| [`override` modifier](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-3.html) | 4.3 | ❌ | ❌ | ✅ | ❌ | ✅ |
| [`out` variance annotation](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-7.html) | 4.7 | ❌ | ✅ | ❌ | ✅ | ❌ |
| [`using` declaration](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-2.html) | 5.2 | ❌ | ❌ | ✅ | ❌ | ❌ |

