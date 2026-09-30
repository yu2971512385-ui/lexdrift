"""The category mappings of the out-of-process adapters.

These run without Node or Go: what matters here is that each adapter turns
its library's token names into the right lexdrift categories, above all that
"this is just an identifier" becomes ``plain``. Mapping that wrong is how a
checker starts inventing gaps.
"""

from __future__ import annotations

from lexdrift.adapters import available_names
from lexdrift.adapters.base import map_category
from lexdrift.adapters.chroma import CATEGORY_MAP as CHROMA_MAP
from lexdrift.adapters.chroma import _longest_prefix
from lexdrift.adapters.node import ACE_CATEGORY_MAP, HLJS_CATEGORY_MAP, PRISM_CATEGORY_MAP


def test_every_shipped_adapter_is_registered():
    assert set(available_names()) == {"ace", "chroma", "highlightjs", "prism", "pygments"}


def test_highlightjs_mapping():
    assert map_category("keyword", HLJS_CATEGORY_MAP) == "keyword"
    assert map_category("type", HLJS_CATEGORY_MAP) == "type"
    assert map_category("built_in", HLJS_CATEGORY_MAP) == "builtin"
    assert map_category("", HLJS_CATEGORY_MAP) == "plain"
    # hljs nests scopes; the dotted name must fall back to its first part
    assert map_category("title.function_", HLJS_CATEGORY_MAP) == "other"
    assert map_category("params", HLJS_CATEGORY_MAP) == "plain"


def test_prism_mapping():
    assert map_category("keyword", PRISM_CATEGORY_MAP) == "keyword"
    assert map_category("class-name", PRISM_CATEGORY_MAP) == "type"
    assert map_category("triple-quoted-string", PRISM_CATEGORY_MAP) == "string"
    assert map_category("", PRISM_CATEGORY_MAP) == "plain"


def test_ace_mapping():
    assert map_category("keyword", ACE_CATEGORY_MAP) == "keyword"
    assert map_category("keyword.operator", ACE_CATEGORY_MAP) == "operator"
    assert map_category("support.type", ACE_CATEGORY_MAP) == "type"
    assert map_category("support.function", ACE_CATEGORY_MAP) == "builtin"
    assert map_category("identifier", ACE_CATEGORY_MAP) == "plain"
    assert map_category("constant.numeric", ACE_CATEGORY_MAP) == "number"
    assert map_category("invalid.illegal", ACE_CATEGORY_MAP) == "error"


def test_chroma_mapping_uses_the_longest_prefix():
    # chroma writes Pygments' names without the dots, so prefixes overlap.
    assert _longest_prefix("KeywordDeclaration") == "keyword"
    assert _longest_prefix("KeywordType") == "type"
    assert _longest_prefix("NameBuiltin") == "builtin"
    assert _longest_prefix("NameOther") == "plain"
    assert _longest_prefix("Name") == "plain"
    assert _longest_prefix("LiteralStringDouble") == "string"
    assert _longest_prefix("LiteralNumberInteger") == "number"
    assert _longest_prefix("Error") == "error"
    assert _longest_prefix("SomethingUnheardOf") == "other"


def test_chroma_map_covers_the_categories_the_corpus_expects():
    assert set(CHROMA_MAP.values()) >= {"keyword", "type", "builtin", "string", "number", "plain"}
