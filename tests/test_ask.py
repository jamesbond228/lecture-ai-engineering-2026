from types import SimpleNamespace

import app.ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=34),
        text="回答",
    )
    chat = SimpleNamespace(send_message=lambda question: response)
    client = SimpleNamespace(chats=SimpleNamespace(create=lambda model: chat))
    monkeypatch.setattr(ask_module.genai, "Client", lambda api_key: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    result = ask_module.ask("質問")

    assert result == "回答"
    assert "入力: 12, 出力: 34" in capsys.readouterr().out


def test_chat_mode_reuses_session_for_follow_up_questions(monkeypatch, capsys):
    questions = []

    def send_message(question):
        questions.append(question)
        return SimpleNamespace(
            usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=34),
            text=f"回答: {question}",
        )

    chat = SimpleNamespace(send_message=send_message)
    client = SimpleNamespace(chats=SimpleNamespace(create=lambda model: chat))
    monkeypatch.setattr(ask_module.genai, "Client", lambda api_key: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("sys.argv", ["app.ask", "最初の質問", "--chat"])
    inputs = iter(["続きの質問", ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

    ask_module.main()

    assert questions == ["最初の質問", "続きの質問"]
    assert "回答: 続きの質問" in capsys.readouterr().out