"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 回答のあとも会話を続ける

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import os

from google import genai
from google.genai import errors
from openai import APIStatusError, OpenAI

from app.config import (
    DEFAULT_OPENROUTER_MODEL,
    MODEL,
    OPENROUTER_BASE_URL,
    PROVIDER,
    api_error_message,
    get_api_key,
    get_openrouter_api_key,
)

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


class OpenRouterChat:
    """OpenRouter の Chat Completions を会話履歴付きで呼び出す。"""

    def __init__(self, client: OpenAI):
        self.client = client
        self.messages: list[dict[str, str]] = []
        self.provider = "openrouter"

    def send_message(self, question: str):
        self.messages.append({"role": "user", "content": question})
        response = self.client.chat.completions.create(
            model=MODEL,
            messages=self.messages,
        )
        message = response.choices[0].message
        self.messages.append({"role": "assistant", "content": message.content or ""})
        return response


class GeminiWithOpenRouterFallback:
    """Gemini を優先し、API エラー時は会話を引き継いで OpenRouter に切り替える。"""

    def __init__(self, gemini_chat):
        self.gemini_chat = gemini_chat
        self.openrouter_chat = None
        self.history: list[dict[str, str]] = []
        self.provider = "gemini"

    def send_message(self, question: str):
        if self.openrouter_chat is None:
            try:
                response = self.gemini_chat.send_message(question)
            except errors.APIError:
                if not os.getenv("OPENROUTER_API_KEY"):
                    raise
                print(
                    "[fallback] Gemini API エラーのため、"
                    f"OpenRouter（{DEFAULT_OPENROUTER_MODEL}）に切り替えます。"
                )
                client = OpenAI(
                    api_key=get_openrouter_api_key(),
                    base_url=OPENROUTER_BASE_URL,
                )
                self.openrouter_chat = OpenRouterChat(client)
                self.openrouter_chat.messages = list(self.history)
                self.provider = "openrouter"
                response = self.openrouter_chat.send_message(question)
        else:
            response = self.openrouter_chat.send_message(question)

        if self.provider == "openrouter":
            answer = response.choices[0].message.content or ""
        else:
            answer = response.text or ""
        self.history.extend(
            [
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer},
            ]
        )
        return response


def create_chat():
    if PROVIDER == "openrouter":
        client = OpenAI(
            api_key=get_openrouter_api_key(),
            base_url=OPENROUTER_BASE_URL,
        )
        return client, OpenRouterChat(client)
    if PROVIDER != "gemini":
        raise SystemExit(
            f"未対応の AIE_PROVIDER: {PROVIDER}。gemini または openrouter を指定してください。"
        )
    client = genai.Client(api_key=get_api_key())
    return client, GeminiWithOpenRouterFallback(client.chats.create(model=MODEL))


def ask(question: str, chat=None) -> str:
    if chat is None:
        client, chat = create_chat()
    response = chat.send_message(question)
    provider = getattr(chat, "provider", PROVIDER)
    if provider == "openrouter":
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else "不明"
        output_tokens = usage.completion_tokens if usage else "不明"
        print(f"[トークン数] 入力: {input_tokens}, 出力: {output_tokens}")
        return response.choices[0].message.content or ""

    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage else "不明"
    output_tokens = usage.candidates_token_count if usage else "不明"
    print(f"[トークン数] 入力: {input_tokens}, 出力: {output_tokens}")

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument("--chat", action="store_true", help="回答のあとも会話を続ける")
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        client, chat = create_chat()
        question = args.question
        while question:
            print(f"[質問] {question}\n")
            print(ask(question, chat))
            if not args.chat:
                break
            try:
                question = input("\n次の質問（終了するには空欄）: ").strip()
            except EOFError:
                break
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)
    except APIStatusError as e:
        print(api_error_message(e.status_code, str(e)))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
