"""The checker turns token streams into verdicts; these pin the verdicts."""

from __future__ import annotations

from lexdrift.check import check, check_feature, check_library
from lexdrift.model import Feature, Status, Token


def feature(**overrides) -> Feature:
    base = dict(
        id="go-any",
        language="go",
        name="predeclared type `any`",
        snippet="var payload any = 1\n",
        token="any",
        since="1.18",
    )
    base.update(overrides)
    return Feature(**base)


def test_recognised_token_is_ok(fake_adapter):
    adapter = fake_adapter({"any": "type"})
    result = check_feature(adapter, feature(expect=("type", "keyword")))
    assert result.status is Status.OK
    assert result.found_category == "type"


def test_plain_token_is_a_gap(fake_adapter):
    result = check_feature(fake_adapter(), feature())
    assert result.status is Status.UNSTYLED
    assert result.is_gap
    assert "plain text" in result.detail


def test_unexpected_category_is_advisory_not_a_gap(fake_adapter):
    adapter = fake_adapter({"any": "other"})
    result = check_feature(adapter, feature(expect=("type",)))
    assert result.status is Status.MISCATEGORISED
    assert not result.is_gap
    assert "expected type" in result.detail


def test_any_recognised_category_passes_without_expectations(fake_adapter):
    adapter = fake_adapter({"any": "other"})
    assert check_feature(adapter, feature()).status is Status.OK


def test_error_tokens_beat_everything(fake_adapter):
    adapter = fake_adapter({"any": "type", "payload": "error"})
    result = check_feature(adapter, feature(expect=("type",)))
    assert result.status is Status.ERROR_TOKEN
    assert result.is_gap


def test_partly_plain_token_counts_as_missing(fake_adapter):
    # `c"x"` where only the quoted part is a string: the prefix is the feature.
    adapter = fake_adapter({'"': "string", "x": "string"}, languages=("rust",))
    result = check_feature(
        adapter,
        feature(id="rust-c-string", language="rust", snippet='let s = c"x";\n', token='c"x"'),
    )
    assert result.status is Status.UNSTYLED
    assert "only partly recognised" in result.detail


def test_baseline_turns_a_style_choice_into_not_applicable(fake_adapter):
    # The library styles no operator at all, old or new: not drift.
    adapter = fake_adapter(languages=("python",))
    result = check_feature(
        adapter,
        feature(
            id="py-walrus",
            language="python",
            snippet="if (size := 3) > 1:\n    pass\n",
            token=":=",
            expect=("operator",),
            baseline_snippet="if size == 3:\n    pass\n",
            baseline_token="==",
        ),
    )
    assert result.status is Status.NOT_APPLICABLE
    assert not result.is_gap


def test_baseline_keeps_a_real_gap_a_gap(fake_adapter):
    # The library does style the old operator, so the new one is drift.
    adapter = fake_adapter({"==": "operator"}, languages=("python",))
    result = check_feature(
        adapter,
        feature(
            id="py-walrus",
            language="python",
            snippet="if (size := 3) > 1:\n    pass\n",
            token=":=",
            expect=("operator",),
            baseline_snippet="if size == 3:\n    pass\n",
            baseline_token="==",
        ),
    )
    assert result.status is Status.UNSTYLED


def test_unknown_language_is_skipped_not_failed(fake_adapter):
    adapter = fake_adapter(languages=("go",))
    result = check_feature(adapter, feature(language="cobol"))
    assert result.status is Status.SKIPPED
    assert not result.is_gap


def test_library_report_counts_and_coverage(fake_adapter):
    adapter = fake_adapter({"any": "type"})
    features = [feature(), feature(id="go-other", token="payload")]
    report = check_library(adapter, features)
    assert report.version == "1.2.3"
    assert report.recognised == 1
    assert len(report.gaps) == 1
    assert report.coverage == 0.5


def test_check_runs_every_adapter(fake_adapter):
    reports = check([fake_adapter({"any": "type"}), fake_adapter()], [feature()])
    assert [report.coverage for report in reports] == [1.0, 0.0]
