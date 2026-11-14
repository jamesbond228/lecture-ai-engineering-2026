"""講座全体で共通のモデル・API設定。"""

import os

# Gemini を既定とし、環境変数で OpenRouter に切り替えられる。
DEFAULT_PROVIDER = "gemini"
DEFAULT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_OPENROUTER_MODEL = "baidu/ernie-5.5-flash-preview:free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
PROVIDER = os.getenv("AIE_PROVIDER", DEFAULT_PROVIDER).strip().lower()
MODEL = os.getenv(
    "AIE_MODEL",
    DEFAULT_OPENROUTER_MODEL if PROVIDER == "openrouter" else DEFAULT_MODEL,
)


def build_model(model_name: str | None = None):
    """選択中のプロバイダーに対応する Pydantic AI モデルを作る。"""
    name = model_name or MODEL
    if PROVIDER == "gemini":
        from pydantic_ai.models.google import GoogleModel
        from pydantic_ai.providers.google import GoogleProvider

        return GoogleModel(name, provider=GoogleProvider(api_key=get_api_key()))
    if PROVIDER == "openrouter":
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider

        return OpenAIChatModel(
            name,
            provider=OpenAIProvider(
                api_key=get_openrouter_api_key(),
                base_url=OPENROUTER_BASE_URL,
            ),
        )
    raise SystemExit(
        f"未対応の AIE_PROVIDER: {PROVIDER}。gemini または openrouter を指定してください。"
    )


def api_error_message(status: int, detail: str = "") -> str:
    """HTTPステータスコードを、受講生向けの日本語の説明にする（ask.py と agent.py で共用）。"""
    if status == 429:
        return "レート制限に達しました。1分ほど待ってから再実行してください。"
    if status == 503:
        return "モデルが混み合っています（503）。少し待ってから再実行してください。"
    if status in (400, 401, 403, 404):
        return f"APIキーかモデル名に問題があります（{status}）: {detail}"
    return f"APIエラー（{status}）: {detail}"


def get_api_key() -> str:
    """環境変数 GEMINI_API_KEY を返す。未設定なら手順を表示して終了する。"""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise SystemExit(
            "環境変数 GEMINI_API_KEY が見つかりません。\n"
            "1. GitHub の Settings → Codespaces → Secrets に GEMINI_API_KEY を登録し、\n"
            "   使う repository に自分の fork を選んでください。\n"
            "2. Codespaces を起動したあとに登録した場合は、Codespaces を再起動してください。\n"
            "   （左下の「Codespaces」→「Stop Current Codespace」→ 再度開く）"
        )
    return key


def get_openrouter_api_key() -> str:
    """環境変数 OPENROUTER_API_KEY を返す。未設定なら設定方法を表示して終了する。"""
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit(
            "環境変数 OPENROUTER_API_KEY が見つかりません。\n"
            "OpenRouter の API キーを Codespaces secret または環境変数に設定してください。\n"
            "キーをコードやチャット、コミットに書かないでください。"
        )
    return key
