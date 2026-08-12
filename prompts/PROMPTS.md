# Prompt templates in the supplied experimental source

This document reproduces the active prompt templates present in the supplied source notebook. The language is preserved as implemented. Ten few-shot examples are prepended for each question type when `n_shots=10`; those JSONL messages must also be released for complete request-level reproduction.

## System message

```text
You are BioASQ-GPT, an AI expert in question answering in the biomedical domain.
```

## Yes/no — AMBI map prompt

```text
Based on the following biomedical evidence snippets:
{batch_snippets}

Question: {question}

Please follow these rules strictly:
1. First output the lowercase word 'yes' or 'no'.
2. Immediately follow it with one short sentence explaining the reason for your choice.
3. If you are uncertain, you must still choose the most likely answer.

Your answer:
```

## Yes/no — SEC reduce prompt used in the reported source

```text
以下是对同一问题的多个分段回答：{map_answers}

问题：{question}

请严格按以下规则给出最终回答：
1. 仅允许输出小写单词 'yes' 或 'no'
2. 禁止添加任何解释、标点或格式修饰
3. 如果所有答案一致，则直接采纳该答案
4. 如果答案存在分歧，请优先选择与问题语义最契合、最合理的答案，而不是简单多数投票
5. 如果只有一个回答，也需基于其合理性判断是否作为最终答案

你的最终回答：
```

## Yes/no — direct prompt when AMBI is not triggered

```text
基于以下医学资料片段：
{snippets}

问题：{question}

请严格按以下规则回答：
1. 仅允许输出小写单词 'yes' 或 'no'
2. 禁止添加任何解释、标点或格式修饰
3. 不确定时仍必须选择最可能的答案

你的回答：
```

## Factoid — AMBI map prompt

```text
基于以下医学资料片段：
{batch_snippets}

问题：'{question}'

请严格按照以下要求回答：
1. 返回一个仅包含 "entities" 键的 JSON 对象。
2. "entities" 的值必须是一个数组，包含 0-5 个候选答案。
3. 候选答案要求：
- 必须直接回答问题（如疾病名、基因名、数值、药物名、解剖结构等）。
- 禁止返回解释性短语、定义或完整句子。
- 如果存在常见的等价表述（如全称/缩写），可以同时返回。
- 按置信度从高到低排序。
4. JSON 必须严格有效：
- 使用双引号
- 无额外文本或注释
- 可被标准 JSON 解析器正确解析
5. 如果无法确定答案，返回空数组：{"entities": []}

示例1：
问题：What is the use of lebrikizumab?
响应：{"entities": ["atopic dermatitis treatment"]}

示例2：
问题：Coffee Bean Sign is characteristic to which disease?
响应：{"entities": ["sigmoid volvulus"]}
```

## Factoid — SEC reduce prompt

```text
以下是候选实体列表（可能重复或包含噪音）：
{map_results}

问题：'{question}'

请严格按以下要求给出最终答案：
1. 仅对候选实体去重和规范化，不要合并或抽象
2. 按出现频率或置信度从高到低排序，最多保留5个
3. 返回一个JSON对象，格式：
{"entities": ["Answer 1", "Answer 2"]}
4. 每个实体必须与候选实体中出现过的内容保持一致，不能自己生成新答案
5. 禁止添加任何解释文字，只输出JSON
```

## List — AMBI map prompt

```text
基于以下医学资料片段：
{batch_snippets}

问题：{question}

请严格按以下要求回答：
1. 返回严格符合此格式的JSON：{"entities": ["实体1", "实体2"]}
2. 实体必须与问题语义严格对应：
- 如果问题询问“疾病/综合征”，只返回疾病/综合征名称。
- 如果问题询问“基因/突变”，只返回基因或突变名称。
- 如果问题询问“方法/手术/治疗”，只返回方法或手术名称。
- 如果问题询问“症状/体征”，只返回症状或体征。
- 如果问题询问“药物/成分/分子”，只返回药物名或活性成分。
- 如果问题询问“来源”，只返回生物学或组织来源。
- 如果问题询问“受体/靶点”，只返回分子受体或通路。
3. 返回的实体必须与问题要求的层次一致（不要列出更低层级的步骤、功能或作用机制）。
4. 按文献中出现频率排序（高频在前）。
5. 每个实体必须是简洁的名词短语（2-5个单词）。
6. 最多返回100个不同实体。
7. 输出中不要包含任何解释性文字。

[示例1]
问题：What are the common symptoms of COVID-19?
响应：{"entities": ["fever", "cough", "fatigue", "loss of smell"]}

[示例2]
问题：List the methods for pectus excavatum repair?
响应：{"entities": ["Nuss procedure", "Ravitch procedure", "sternotomy", "vacuum bell"]}
```

## List — SEC reduce prompt

```text
以下是候选实体列表（可能重复或包含噪音）：
{map_entities}

问题：{question}

请严格按以下要求给出最终答案：
1. 对候选实体仅做去重和规范化，不要概括、合并或抽象
2. 按出现频率从高到低排序，保留前 100 个
3. 返回严格符合 JSON 格式：{"entities": ["实体1", "实体2"]}
4. 每个实体必须与候选实体中出现过的内容保持一致，不能自己生成新实体
5. 禁止添加任何解释文字，只输出 JSON
```
