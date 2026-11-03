# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
第1回

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
[usage] RunUsage(cost=Decimal('0.0007538'), details={'text_prompt_tokens': 1196}, input_text_tokens=1196, input_tokens=1196, output_tokens=158, requests=2, tool_calls=2)

- 1つの質問での LLM 呼び出し回数（`requests`）：


- 追加したツールと、docstring に書いた説明：

## 宿題

- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：
- 結果：
- 気づき・疑問：
