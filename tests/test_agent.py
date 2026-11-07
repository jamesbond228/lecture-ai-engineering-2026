"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、登録されたツールを全部呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.agent import agent

BASE_TOOLS = {"search_glossary", "get_lecture_summary", "make_quiz", "save_learning_log"}


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_base_tools_are_registered_and_called():
    model = TestModel()
    with agent.override(model=model):
        result = agent.run_sync("LoRAとは？")

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert BASE_TOOLS <= offered  # 演習でツールを足しても壊れないよう「含む」で判定

    called = {p.tool_name for p in _parts(result, ToolCallPart)}
    assert BASE_TOOLS <= called
    # 承認が必要なツール（requires_approval=True）は、実行されずに承認待ちになるので戻り値が無い
    waiting = len(result.output.approvals) if isinstance(result.output, DeferredToolRequests) else 0
    assert len(_parts(result, ToolReturnPart)) + waiting == len(_parts(result, ToolCallPart))
    assert result.output


def test_glossary_result_reaches_the_model():
    model = TestModel(call_tools=["search_glossary"])
    with agent.override(model=model):
        result = agent.run_sync("RAGとは？")
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == "search_glossary"


def test_learning_log_waits_for_approval_before_saving(tmp_path, monkeypatch):
    """保存ツールは呼び出し時に止まり、承認結果を渡したあとで初めて保存する。"""
    from app import tools

    # 実際の learning_log/ は汚さず、一時フォルダへの保存をテストする。
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path / "learning_log")
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        result = agent.run_sync("学んだことを記録して")

    # DeferredToolRequests は「ツールを実行する前に、人の判断が必要」という保留中の結果。
    assert isinstance(result.output, DeferredToolRequests)
    assert [call.tool_name for call in result.output.approvals] == ["save_learning_log"]
    # 承認前なので、保存先フォルダすらまだ作られていない。
    assert not (tmp_path / "learning_log").exists()

    # 承認結果は、保留になったツール呼び出しと同じ ID に結びつけて渡す。
    approval = result.output.approvals[0]
    deferred_results = result.output.build_results(approvals={approval.tool_call_id: True})
    # 直前までの会話と承認結果を渡すと、エージェントは保留中の処理を再開する。
    with agent.override(model=TestModel(call_tools=[])):
        resumed = agent.run_sync(
            None,
            message_history=result.all_messages(),
            deferred_tool_results=deferred_results,
        )

    assert isinstance(resumed.output, str)
    saved_files = list((tmp_path / "learning_log").glob("*.md"))
    assert len(saved_files) == 1


def test_learning_log_is_not_saved_when_approval_is_rejected(tmp_path, monkeypatch):
    """利用者が拒否した場合は、保留中の保存ツールを実行しない。"""
    from app import tools

    # テスト専用の一時フォルダを保存先にする。
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path / "learning_log")
    with agent.override(model=TestModel(call_tools=["save_learning_log"])):
        result = agent.run_sync("学んだことを記録して")

    assert isinstance(result.output, DeferredToolRequests)
    approval = result.output.approvals[0]
    # False は拒否を表す。実行結果をエージェントに返し、会話を再開する。
    deferred_results = result.output.build_results(approvals={approval.tool_call_id: False})
    with agent.override(model=TestModel(call_tools=[])):
        agent.run_sync(
            None,
            message_history=result.all_messages(),
            deferred_tool_results=deferred_results,
        )

    # 拒否されたので、ディレクトリもファイルも作られない。
    assert not (tmp_path / "learning_log").exists()
