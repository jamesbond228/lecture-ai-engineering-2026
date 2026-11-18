# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
第1回は最もらしい回答が生成されるが、今回は用語集を参照して"id": "homework-levels"を引用して回答した。
エージェント
AIE2026の宿題における「3レベル」とは、宿題の難易度や目的別に用意された以下の3つの段階のことです。
1. **基礎**：講義内容の確認を行うレベル
2. **実装**：自分でコードを書くレベル
3. **発展**：さらに調査や試行を行うレベル
3つのうち**どれか1つに取り組めばその回の宿題は完了**となります（原則として採点は行われません）。ご自身の理解度や使える時間に合わせて、どのレベルに取り組むか選んでみてください。

- `--trace` で見えたツール呼び出し（ツール名と引数）：
[tool call]   search_glossary({'query': 'LoRA'})
[tool call]   search_glossary({'query': 'QLoRA'})
[tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, "definition": "事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラ…
[tool return] search_glossary -> [{"term": "QLoRA", "lecture": 2, "definition": "ベースモデルの重みを4ビットなどに量子化してメモリを節約したうえで、LoRAで学習する手法。より大きなモデルを小さなGPUで扱える。本講座の第2…

- 1つの質問での LLM 呼び出し回数（`requests`）：
2回
[usage] RunUsage(cost=Decimal('0.0007538'), details={'text_prompt_tokens': 1196}, input_text_tokens=1196, input_tokens=1196, output_tokens=158, requests=2, tool_calls=2)

- 追加したツールと、docstring に書いた説明：
def make_quiz(lecture: int) -> str:
    """指定した回の用語集から1つを選び、意味を問う確認問題と答えを返す。

    「第2回の確認問題を出して」のように、指定した回の復習問題を求められたときに使う。
    """
    terms = [term for term in load_glossary() if term["lecture"] == lecture]
    if not terms:
        return f"第{lecture}回の用語が用語集に見つかりませんでした。"

    term = random.choice(terms)
    return f"問題: 「{term['term']}」の意味は？\n答え: {term['definition']}"

## 宿題

- 取り組んだレベル：基礎 / 実装 / 発展
実装
- やったこと：
copilotに実装指示。以下が生成され、pytestを通過したが、実装したコードの理解が浅く、コードの補足説明の追加を指示。
保存を確認する段階では、実際の learning_log/ は汚さず、一時フォルダへの保存して、承認待ち状態に移行することを確認。
agent.py
def load_mcp_servers(config_path: Path = MCP_CONFIG) -> list[MCPToolset]:
    """設定ファイル（mcpServers 形式）を読み、サーバーごとに接続（MCPToolset）を作る。
tool.py
def test_learning_log_waits_for_approval_before_saving(tmp_path, monkeypatch):
    """保存ツールは呼び出し時に止まり、承認結果を渡したあとで初めて保存する。"""
def test_learning_log_is_not_saved_when_approval_is_rejected(tmp_path, monkeypatch):
    """利用者が拒否した場合は、保留中の保存ツールを実行しない。"""

- 結果：
学習記録について、正常出力されたが、学習記録の日時をでたらめに提案してきた。
保存ツールの実行日をyyyy/mm/dd 形式で自動記録するように修正。すると、save_learning_log が呼ばれず、エージェントが文章だけで保存確認をしていた。
保存を明示的に依頼されたら save_learning_log を必ず呼び、承認確認はツール側に任せるよう、agent.py の指示と tools.py の docstring を修正した。
結果、以下の出力が得られ、日時も正確に記録できていることを確認した。
uv run python -m app.agent --trace "次の内容を学習記録に保存してください: 第3回の確認問題でMCPについて復習した"
[model] gemini-3.5-flash-lite

save_learning_log の実行要求:
{
  "content": "第3回の確認問題でMCPについて復習した"
}
この学習記録を保存しますか？ [y/N]: y
学習内容を記録しました。

（関連する回：第3回）
--- trace ---
[tool call]   save_learning_log({'content': '第3回の確認問題でMCPについて復習した'})
[tool return] save_learning_log -> 学習記録を保存しました: learning_log/20261107-030337-6de324de929d43e0a1714a30ed49297d.md…
[usage] RunUsage(cost=Decimal('0.0002506'), details={'text_prompt_tokens': 702}, input_text_tokens=702, input_tokens=702, output_tokens=16, requests=1, tool_calls=1)

- 気づき・疑問：
実装指示の文面で、アーキテクチャに起こして指示せずとも、意図をくみ取ってコード生成している。
ただし、細かい配慮に欠けるため、満足する実装できなかった。出力確認→改善の重要性を学んだ。
Quriの推奨ワークフローとして、PlanまたはChatで設計 → 人間が承認 → AgentまたはCoding agentで実装が適切。
目的と品質基準は人間が決め、エージェントには限定された計画・実行・確認を任せる方針を推奨された。
copilotを使いこなせておらず、オフィスアワーで質問したい。
もう一度、上記と同じ実装を、推奨手順で実装すると、コードや所要時間に差がどれほど出るか？