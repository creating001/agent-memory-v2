# Agent-Memory Experiment Protocol

本文档记录 Agent-Memory 实验中需要统一固定的公共设置。后续方法迭代时，默认只改变 memory 方法本身；下面这些设置应保持一致。

## 1. 模型协议

### Answer 模型

```yaml
answer:
  name: Qwen/Qwen3.6-35B-A3B
  service: local_vllm_generation
  temperature: 0.0
  max_input_tokens: 131072
  max_output_tokens: 16384
  thinking: disabled
  chat_template_kwargs:
    enable_thinking: false
```

### Embedding 模型

```yaml
embedding:
  name: Qwen/Qwen3-Embedding-0.6B
  service: local_vllm_embedding
  dims: 1024
  normalize: true
  max_input_length: 32768
```

### Rerank 模型

```yaml
rerank:
  name: Qwen/Qwen3-Reranker-0.6B
  service: local_rerank_service
```

### Judge 模型

```yaml
judge:
  models:
    flash_1: deepseek-v4-flash
    flash_2: deepseek-v4-flash
  service: api
  temperature: 0.0
  thinking:
    flash_1: default
    flash_2: default
  report:
    strict_accuracy: both_judges_correct
    lenient_accuracy: either_judge_correct
    single_judge_accuracy: diagnostic_only
```

正式实验默认使用 `deepseek-v4-flash` 独立跑两遍离线 judge：

- `strict_accuracy`：两个 judge 都判为 `CORRECT` 才算正确。
- `lenient_accuracy`：任一 judge 判为 `CORRECT` 即算正确。
- 两遍 flash 的单次 accuracy 只作为诊断指标，用于定位 judge 随机分歧，不作为唯一主指标。
- judge 只能读取已经完成的 prediction 和 gold labels，不能进入 prediction、retrieval、compiler、answer、verifier 或 cache build 流程。

### 部署规划

```yaml
deployment:
  answer:
    model: Qwen/Qwen3.6-35B-A3B
    service: local_vllm_generation
    cuda_visible_devices: [0, 1, 2, 3]
    tensor_parallel_size: 4
    gpu_memory_utilization: 0.8
    max_model_len: 131072
    max_output_tokens: 16384
    request_chat_template_kwargs:
      enable_thinking: false

  embedding:
    model: Qwen/Qwen3-Embedding-0.6B
    service: local_vllm_embedding
    cuda_visible_devices: [4]
    gpu_memory_utilization: 0.8

  rerank:
    model: Qwen/Qwen3-Reranker-0.6B
    service: local_rerank_service
    cuda_visible_devices: [5]
    gpu_memory_utilization: 0.8
```

部署时默认 Answer LLM 独占 GPU 0-3，embedding 独占 GPU 4，rerank 独占 GPU 5。`gpu_memory_utilization` 是服务启动时的目标显存占用上限；如果 rerank 后端不支持该参数，就合理限制一下。

## 2. Prompt Template 协议

### LoCoMo Judge Template

```text
Your task is to label an answer to a question as 'CORRECT' or 'WRONG'. You will be given the following data:
    (1) a question (posed by one user to another user),
    (2) a 'gold' (ground truth) answer,
    (3) a generated answer
which you will score as CORRECT/WRONG.

The point of the question is to ask about something one user should know about the other user based on their prior conversations.
The gold answer will usually be a concise and short answer that includes the referenced topic, for example:
Question: Do you remember what I got the last time I went to Hawaii?
Gold answer: A shell necklace
The generated answer might be much longer, but you should be generous with your grading - as long as it touches on the same topic as the gold answer, it should be counted as CORRECT.

For time related questions, the gold answer will be a specific date, month, year, etc. The generated answer might be much longer or use relative time references (like "last Tuesday" or "next month"), but you should be generous with your grading - as long as it refers to the same date or time period as the gold answer, it should be counted as CORRECT. Even if the format differs (e.g., "May 7th" vs "7 May"), consider it CORRECT if it's the same date.

Now it's time for the real question:
Question: {question}
Gold answer: {gold_answer}
Generated answer: {generated_answer}

Return exactly one label: CORRECT or WRONG.
Do not include explanations, JSON, markdown, code fences, or any other text.
```

### LongMemEval Judge Templates

#### single-session-user / single-session-assistant / multi-session

```text
I will give you a question, a correct answer, and a response from a model. Please answer yes if the response contains the correct answer. Otherwise, answer no. If the response is equivalent to the correct answer or contains all the intermediate steps to get the correct answer, you should also answer yes. If the response only contains a subset of the information required by the answer, answer no.

Question: {question}

Correct Answer: {answer}

Model Response: {response}

Is the model response correct? Answer yes or no only.
```

#### temporal-reasoning

```text
I will give you a question, a correct answer, and a response from a model. Please answer yes if the response contains the correct answer. Otherwise, answer no. If the response is equivalent to the correct answer or contains all the intermediate steps to get the correct answer, you should also answer yes. If the response only contains a subset of the information required by the answer, answer no. In addition, do not penalize off-by-one errors for the number of days. If the question asks for the number of days/weeks/months, etc., and the model makes off-by-one errors (e.g., predicting 19 days when the answer is 18), the model's response is still correct.

Question: {question}

Correct Answer: {answer}

Model Response: {response}

Is the model response correct? Answer yes or no only.
```

#### knowledge-update

```text
I will give you a question, a correct answer, and a response from a model. Please answer yes if the response contains the correct answer. Otherwise, answer no. If the response contains some previous information along with an updated answer, the response should be considered as correct as long as the updated answer is the required answer.

Question: {question}

Correct Answer: {answer}

Model Response: {response}

Is the model response correct? Answer yes or no only.
```

#### single-session-preference

```text
I will give you a question, a rubric for desired personalized response, and a response from a model. Please answer yes if the response satisfies the desired response. Otherwise, answer no. The model does not need to reflect all the points in the rubric. The response is correct as long as it recalls and utilizes the user's personal information correctly.

Question: {question}

Rubric: {answer}

Model Response: {response}

Is the model response correct? Answer yes or no only.
```

#### abstention

```text
I will give you an unanswerable question, an explanation, and a response from a model. Please answer yes if the model correctly identifies the question as unanswerable. The model could say that the information is incomplete, or some other information is given but the asked information is not.

Question: {question}

Explanation: {answer}

Model Response: {response}

Does the model correctly identify the question as unanswerable? Answer yes or no only.
```

## 3. 指标协议

```yaml
retrieval:
  top_k: must_report

metrics:
  strict_accuracy

  lenient_accuracy

  flash_1_accuracy_diagnostic

  flash_2_accuracy_diagnostic

  f1

  bleu

  by_type:
    group_by: question_type_or_category
    fields: [strict_accuracy, lenient_accuracy, flash_1_accuracy_diagnostic, flash_2_accuracy_diagnostic, f1, bleu]

  token_cost:
    fields:
      - build_tokens
      - query_tokens
      - build_think_tokens
      - query_think_tokens
      - build_total_tokens
      - query_total_tokens
    note: build_tokens/query_tokens are visible LLM tokens. Think tokens are counted separately when explicitly reported by the provider.
```
