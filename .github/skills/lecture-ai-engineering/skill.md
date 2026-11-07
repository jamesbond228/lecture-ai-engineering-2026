---
name: lecture-ai-engineering-2026
description: AIエンジニアリング実践講座2026の開発・演習用リポジトリに対する作業を支援するためのスキル。
---

# lecture-ai-engineering-2026 開発スキル

このリポジトリは、LLM / AIエージェントの実践講座用の演習・宿題用リポジトリです。
主な目的は、APIキーを使ったLLMアプリの作成、ツール呼び出し型エージェントの実装、データセット作成、MCP連携の体験を通じてAIエンジニアリングの基礎を学ぶことです。

## リポジトリの構造

- `app/`: 実際のアプリ本体
  - `app/config.py`: APIキーとモデル名の読み込み
  - `app/ask.py`: 素のLLMに質問するCLI
  - `app/tools.py`: エージェント用ツール群
  - `app/agent.py`: 学習支援エージェント
  - `app/mcp_server.py`: MCPサーバー
- `data/`: 用語集や講義要点データ
  - `data/glossary.json`: 用語集
  - `data/lectures/`: 各回の要点
- `lectures/`: 各回の演習・宿題文書
- `notebooks/`: Colab向けノートブック
- `scripts/`: 補助スクリプト
- `tests/`: APIキー不要で実行できるテスト
- `README.md`: 使い方と全体の導入手順

## はじめ方

前提:
- Python 3.12
- `uv` がインストール済み
- `GEMINI_API_KEY` を設定済み

初期化:

```bash
uv sync --frozen
```

動作確認:

```bash
uv run pytest -q
uv run python -m app.ask "LoRAとは何ですか？"
uv run python -m app.agent --list-tools
```

## 重要な設計思想

- 環境変数を使ってAPIキーやモデル名を管理する
  - `app/config.py` を通して `GEMINI_API_KEY` と `AIE_MODEL` を読む
  - コード中に秘密情報を直書きしない
- LLMの能力は「質問→回答」だけでなく「ツール呼び出し」の利用も学ぶ
  - `app/tools.py` にツール関数を定義する
  - `app/agent.py` で `Agent` に組み込む
- 仕様変更は、講義の回と対応づけて説明できるようにする
  - 単純な機能追加ではなく、講座の学習目的に沿って設計する
- 実際の利用者は受講生であり、手軽に試せるCLI中心の構成を保つ

## コーディング時の指針

- 既存の構造を壊さず、`app/` 配下の責務を意識して変更する
- 新しいツールを追加するなら、`app/tools.py` の docstring と型ヒントを使ってLLMに説明しやすくする
- `Agent` の指示文（`INSTRUCTIONS`）やツール定義を変える場合は、振る舞いが受講生向けに分かりやすくなるようにする
- 仕様を変えるときは、関連する `lectures/` 文書や `README.md` の説明と整合するか確認する
- 実験的なコードやノートブックの変更は、講座の目的に沿う範囲にとどめる

## テストと検証

- 基本は `uv run pytest -q` で確認する
- APIキーが必要な動作の確認は `app.ask` / `app.agent` のCLI経由で行う
- `tests/` は APIキーなしで動く前提で作る
- 変更後は、関連するセルやCLIの入出力が壊れていないかを最低限確認する

## 出力のスタイル

- 日本語で返答する
- 受講生向けに説明し、技術的な背景や使い方も含める
- 例やコマンドを挿入しやすい簡潔な説明にする
- 実装内容の説明は、どの回の講義やどのファイルに対応するかがわかるようにする

## 典型的な修正例

- LLMに渡すプロンプトやツール説明を調整したい
  - `app/agent.py` と `app/tools.py` を確認する
- 学習用データを自動生成したい
  - `scripts/` 配下のスクリプトと `data/` の形式を確認する
- エージェントの新しい機能を追加したい
  - `app/tools.py` にツールを追加し、`app/agent.py` で登録する
- 講義の資料と実装のズレを直したい
  - `lectures/` と `README.md` と実コードの対応を確認する

## 注意事項

- `GEMINI_API_KEY` や `AIE_MODEL` のような設定値は、コミットやPRに含めない
- 生成されたデータやログは、講義用途の範囲で保守する
- 講座の性質上、実演用のCLIやワークフローを優先し、過剰に複雑な抽象化は避ける
