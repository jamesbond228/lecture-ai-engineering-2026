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


def test_openrouter_chat_uses_configured_model_and_tracks_history(monkeypatch, capsys):
    requests = []

    def create_completion(**kwargs):
        requests.append({**kwargs, "messages": [dict(m) for m in kwargs["messages"]]})
        return SimpleNamespace(
            usage=SimpleNamespace(prompt_tokens=5, completion_tokens=7),
            choices=[SimpleNamespace(message=SimpleNamespace(content="回答"))],
        )

    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=create_completion)
        )
    )
    monkeypatch.setattr(ask_module, "PROVIDER", "openrouter")
    monkeypatch.setattr(ask_module, "MODEL", "test/free-model")
    monkeypatch.setattr(ask_module, "OpenAI", lambda **kwargs: client)
    monkeypatch.setattr(ask_module, "get_openrouter_api_key", lambda: "test-key")

    _, chat = ask_module.create_chat()
    assert ask_module.ask("質問", chat) == "回答"

    assert requests[0]["model"] == "test/free-model"
    assert requests[0]["messages"] == [{"role": "user", "content": "質問"}]
    assert "入力: 5, 出力: 7" in capsys.readouterr().out


def test_gemini_falls_back_to_openrouter_and_preserves_chat_history(monkeypatch, capsys):
    requests = []
    primary_responses = iter(
        [
            SimpleNamespace(
                text="Gemini の回答",
                usage_metadata=SimpleNamespace(prompt_token_count=3, candidates_token_count=4),
            ),
            RuntimeError("Gemini API error"),
        ]
    )

    def send_to_gemini(question):
        response = next(primary_responses)
        if isinstance(response, Exception):
            raise response
        return response

    def create_completion(**kwargs):
        requests.append({**kwargs, "messages": [dict(m) for m in kwargs["messages"]]})
        return SimpleNamespace(
            usage=SimpleNamespace(prompt_tokens=5, completion_tokens=7),
            choices=[SimpleNamespace(message=SimpleNamespace(content="OpenRouter の回答"))],
        )

    openrouter_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=create_completion)
        )
    )
    gemini_chat = SimpleNamespace(send_message=send_to_gemini)
    gemini_client = SimpleNamespace(chats=SimpleNamespace(create=lambda model: gemini_chat))
    monkeypatch.setattr(ask_module, "PROVIDER", "gemini")
    monkeypatch.setattr(ask_module, "MODEL", "gemini-test-model")
    monkeypatch.setattr(ask_module.errors, "APIError", RuntimeError)
    monkeypatch.setattr(ask_module.genai, "Client", lambda api_key: gemini_client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "gemini-test-key")
    monkeypatch.setattr(ask_module, "get_openrouter_api_key", lambda: "openrouter-test-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-test-key")
    monkeypatch.setattr(ask_module, "OpenAI", lambda **kwargs: openrouter_client)

    _, chat = ask_module.create_chat()

    assert ask_module.ask("最初の質問", chat) == "Gemini の回答"
    assert ask_module.ask("続きの質問", chat) == "OpenRouter の回答"
    assert requests[0]["messages"] == [
        {"role": "user", "content": "最初の質問"},
        {"role": "assistant", "content": "Gemini の回答"},
        {"role": "user", "content": "続きの質問"},
    ]
    assert "Gemini API エラー" in capsys.readouterr().out
