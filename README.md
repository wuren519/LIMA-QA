# LIMA-QA

Implementation of **LIMA-QA: Mitigating Lost-in-the-Middle for Robust Biomedical Question Answering**.

LIMA-QA is a parameter-free, inference-time framework for multi-snippet biomedical question answering. It is designed for BioASQ Task B exact-answer questions and combines MedCPT-based snippet reranking, LITM-risk pre-checking, adaptive micro-batch inference, and structured answer consolidation without task-specific fine-tuning or modification of the backbone LLM.

## Framework

LIMA-QA consists of four main components:

1. **Snippet Reordering**  
   Retrieved evidence snippets are semantically reranked using MedCPT query and article encoders.

2. **LITM-Risk Pre-check**  
   The pre-check uses snippet displacement after reranking as a risk signal. For questions with more than four snippets, the default middle region is
   \(M=\{3,\ldots,N-2\}\) under one-based indexing. A question is flagged when at least one snippet originally located in this middle region appears in the reranked top-3 positions. The pre-check is disabled for \(N \leq 4\).

3. **Adaptive Micro-Batch Inference (AMBI)**  
   When the LITM-risk signal is triggered, the reranked snippets are divided into small batches before LLM inference. The batching strategy primarily uses batches of two snippets and introduces a batch of three when needed to avoid a residual single-snippet batch.

4. **Structured Entity Consolidation (SEC)**  
   Batch-level predictions are consolidated through question-type-specific constrained reduction. For factoid and list questions, the reduction is restricted to candidates generated at the batch level and is followed by deterministic parsing, normalization, deduplication, and output formatting. No general-knowledge fallback is used in the current implementation.

## Repository Structure

```text
LIMA-QA/
├── README.md
├── requirements.txt
├── .gitignore
├── notebooks/
│   └── limaqa_main_pipeline.ipynb
├── src/
│   ├── rerank_with_medcpt.py
│   └── fix_factoid_exact_answer.py
├── prompts/
│   └── PROMPTS.md
└── data/
    ├── fewshot/
    │   ├── 04_QA_Factoid_11B1-3-4_76.jsonl
    │   ├── 05_QA_Ideal_11B1-3-4_255.jsonl
    │   ├── 06_QA_List_11B1-3-4_54.jsonl
    │   └── 07_QA_YesNo_11B1-3-4_62.jsonl
    ├── Task12B-testData/
    └── Task12BGoldenEnriched/
```

## Requirements

The core Python dependencies are listed in `requirements.txt`:

```text
openai>=1.0
transformers>=4.40
torch>=2.0
pandas>=2.0
tqdm>=4.66
```

Install them with:

```bash
pip install -r requirements.txt
```

The implementation also requires:

- **Ollama** for local model serving
- **DeepSeek-R1:32B** as the backbone LLM
- **MedCPT Query Encoder**
- **MedCPT Article Encoder**
- a CUDA-capable GPU for local inference

The experiments reported in the manuscript were conducted on an NVIDIA RTX A5000 GPU with 24 GB memory.

## Backbone Model

The main inference pipeline uses **DeepSeek-R1:32B** through an OpenAI-compatible local endpoint:

```text
http://127.0.0.1:11434/v1
```

A typical Ollama setup is:

```bash
ollama pull deepseek-r1:32b
ollama serve
```

The sampling temperature is fixed to `0.0`. The API-key string used by the OpenAI client in the notebook is only a placeholder for the local endpoint.

No task-specific fine-tuning or modification of the DeepSeek-R1:32B backbone parameters is required.

## MedCPT Reranking and LITM-Risk Pre-check

`src/rerank_with_medcpt.py` performs semantic reranking with separate MedCPT query and article encoders and computes the `lost_in_the_middle` flag consumed by the main inference pipeline.

The script currently expects local paths to the MedCPT checkpoints. Before execution, set the paths for:

- `MedCPT-Query-Encoder`
- `MedCPT-Article-Encoder`

Then run:

```bash
python src/rerank_with_medcpt.py \
  --input path/to/input.json \
  --output path/to/reranked_output.json
```

For \(N>4\), the default pre-check examines the original middle region \(M=\{3,\ldots,N-2\}\). If at least one of these snippets is promoted into the reranked top-3 positions, `lost_in_the_middle` is set to `True`; otherwise it is set to `False`.

For \(N \leq 4\), the pre-check returns `False`.

## Main Inference Pipeline

The main LIMA-QA inference procedure is provided in:

```text
notebooks/limaqa_main_pipeline.ipynb
```

The notebook contains:

- direct inference for non-triggered questions;
- adaptive micro-batching;
- AMBI batch-level inference;
- SEC reduction for yes/no, factoid, and list questions;
- BioASQ exact-answer parsing and formatting; and
- the ideal-answer functions retained from the original BioASQ pipeline.

The reported LIMA-QA evaluation focuses on exact-answer question types. In the main execution path, ideal-answer generation is disabled.

If Jupyter is not installed:

```bash
pip install jupyter
```

Then launch the notebook and configure the local input/output, few-shot, and model paths for the local environment.

## Adaptive Micro-Batching

The batching procedure is implemented by `get_batch_plan()` in the main notebook.

For up to ten snippets, the plans are:

```text
1  -> [1]
2  -> [2]
3  -> [3]
4  -> [2, 2]
5  -> [2, 3]
6  -> [2, 2, 2]
7  -> [3, 2, 2]
8  -> [2, 2, 2, 2]
9  -> [3, 2, 2, 2]
10 -> [2, 2, 2, 2, 2]
```

The general strategy favors batches of two snippets and uses a batch of three when necessary to avoid leaving a single-snippet residual batch.

## Prompt Templates

The prompt templates corresponding to the implementation are documented in:

```text
prompts/PROMPTS.md
```

The prompts are reproduced in the language used by the implementation. The file includes:

- the system message;
- yes/no AMBI batch-level prompt;
- yes/no SEC reduction prompt;
- direct yes/no prompt;
- factoid AMBI and SEC prompts; and
- list AMBI and SEC prompts.

The few-shot messages prepended to runtime requests are provided separately under `data/fewshot/`.

## Few-Shot Examples

The main pipeline uses:

```text
n_shots = 10
```

The few-shot files are stored in:

```text
data/fewshot/
```

Separate JSONL files are provided for yes/no, factoid, list, and ideal-answer generation. The yes/no, factoid, and list files form part of the exact prompt context used for the reported exact-answer experiments.

## SEC and LLM Calls

For an exact-answer question that does **not** trigger the LITM-risk pre-check, the pipeline performs one direct LLM inference call.

For a triggered question divided into \(m\) adaptive micro-batches:

```text
m batch-level LLM calls
+ 1 SEC reduction call
= m + 1 LLM calls
```

MedCPT reranking and the LITM-risk pre-check themselves do not invoke the LLM.

### Yes/No

Each micro-batch produces a binary prediction and a short rationale. SEC then performs a constrained reduction over the batch-level outputs, with the final output restricted to lowercase `yes` or `no`.

### Factoid and List

Each micro-batch returns candidate entities in JSON format. During SEC reduction, the model is restricted to candidates appearing in the batch-level outputs and is not permitted to generate new candidate entities. Deterministic post-processing then parses, normalizes, deduplicates, and formats the final answer.

No general-knowledge or question-only fallback is used in the current SEC implementation.

## Factoid Output Utility

`src/fix_factoid_exact_answer.py` is a small post-processing utility for converting factoid outputs of the form:

```text
[[A, B, C]]
```

into the BioASQ-compatible form:

```text
[[A], [B], [C]]
```

Set its input and output paths before use.

## Data

The repository includes the BioASQ 12b test inputs used by the pipeline and the corresponding enriched golden-answer files under:

```text
data/Task12B-testData/
data/Task12BGoldenEnriched/
```

Users should follow the BioASQ benchmark's applicable distribution and usage conditions when using these files.

## Reproducibility Summary

- Backbone LLM: `deepseek-r1:32b`
- Sampling temperature: `0.0`
- Few-shot setting: `n_shots = 10`
- Default LITM-risk top-\(k\): `3`
- Default middle region: \(M=\{3,\ldots,N-2\}\)
- LITM-risk pre-check disabled for \(N \leq 4\)
- No task-specific fine-tuning
- No general-knowledge fallback in SEC
- Prompt templates: `prompts/PROMPTS.md`
- Few-shot messages: `data/fewshot/`
- SimpleAgg baseline: `src/simpleagg.py`
