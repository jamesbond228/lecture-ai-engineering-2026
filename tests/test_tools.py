"""ツールのテスト（LLMもAPIキーも使わない）。"""

import json
from datetime import datetime, timezone

from app import tools


def test_glossary_ids_are_unique_and_related_links_exist():
    terms = tools.load_glossary()
    ids = [t["id"] for t in terms]
    assert len(ids) == len(set(ids))
    for t in terms:
        for r in t["related"]:
            assert r in ids, f"{t['id']} の related に存在しない id: {r}"


def test_search_finds_term_by_name_and_alias():
    for query in ["LoRA", "lora", "Low-Rank Adaptation"]:
        hits = json.loads(tools.search_glossary(query))
        assert hits[0]["term"] == "LoRA", query


def test_search_finds_course_specific_term():
    hits = json.loads(tools.search_glossary("lecNN-start"))
    assert hits[0]["term"] == "lecNN-start タグ"


def test_search_limits_number_of_results():
    hits = json.loads(tools.search_glossary("エージェント"))
    assert 1 <= len(hits) <= tools.MAX_RESULTS


def test_search_reports_not_found():
    assert "見つかりませんでした" in tools.search_glossary("存在しない用語xyz")


def test_lecture_summary():
    assert "エージェント" in tools.get_lecture_summary(3)
    assert "まだありません" in tools.get_lecture_summary(99)


def test_make_quiz_uses_a_term_from_the_requested_lecture(monkeypatch):
    terms = tools.load_glossary()
    expected = next(term for term in terms if term["lecture"] == 2)
    chosen_from = []

    def choose(candidates):
        chosen_from.extend(candidates)
        return expected

    monkeypatch.setattr(tools.random, "choice", choose)
    result = tools.make_quiz(2)

    assert chosen_from
    assert all(term["lecture"] == 2 for term in chosen_from)
    assert f"「{expected['term']}」の意味は？" in result
    assert expected["definition"] in result


def test_make_quiz_reports_when_lecture_has_no_terms(monkeypatch):
    monkeypatch.setattr(tools, "load_glossary", lambda: [])
    assert "第99回" in tools.make_quiz(99)
    assert "見つかりませんでした" in tools.make_quiz(99)


def test_save_learning_log_adds_actual_date_and_writes_markdown(tmp_path, monkeypatch):
    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 11, 7, 12, 0, tzinfo=tz or timezone.utc)

    log_dir = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", log_dir)
    monkeypatch.setattr(tools, "datetime", FrozenDateTime)

    result = tools.save_learning_log("今日はエージェントについて学んだ。")

    saved_files = list(log_dir.glob("*.md"))
    assert len(saved_files) == 1
    assert saved_files[0].read_text(encoding="utf-8") == (
        "# 学習記録\n\n"
        "- 日時: 2026/11/07\n\n"
        "今日はエージェントについて学んだ。\n"
    )
    assert result.startswith("学習記録を保存しました: learning_log/")


def test_save_learning_log_uses_tool_date_instead_of_model_supplied_date(tmp_path, monkeypatch):
    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 11, 7, 12, 0, tzinfo=tz or timezone.utc)

    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path / "learning_log")
    monkeypatch.setattr(tools, "datetime", FrozenDateTime)

    tools.save_learning_log(
        "# 学習記録\n\n- 日時: 2026年3月（または直近の日付）\n- 内容: MCPについて復習した"
    )

    saved_file = next((tmp_path / "learning_log").glob("*.md"))
    saved_content = saved_file.read_text(encoding="utf-8")
    assert "- 日時: 2026/11/07" in saved_content
    assert "2026年3月（または直近の日付）" not in saved_content
    assert "- 内容: MCPについて復習した" in saved_content


def test_save_learning_log_rejects_empty_content(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path / "learning_log")

    try:
        tools.save_learning_log("  \n")
    except ValueError as error:
        assert "学習内容" in str(error)
    else:
        raise AssertionError("空の学習内容は保存できない")
    assert not (tmp_path / "learning_log").exists()


def test_default_question_of_lecture1_is_answerable_from_glossary():
    """第1回の既定の質問（app.ask）は、第3回のエージェントが用語集で正しく答えられること。"""
    from app.ask import DEFAULT_QUESTION

    assert "3レベル" in DEFAULT_QUESTION
    hits = json.loads(tools.search_glossary("3レベル"))
    assert hits[0]["term"] == "宿題の3レベル"
