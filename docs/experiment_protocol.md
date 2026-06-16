# Agent-Memory Experiment Protocol

本文档记录 Agent-Memory 实验中需要统一固定的公共设置。后续方法迭代时，默认只改变 memory 方法本身；下面这些设置应保持一致。

## 1. 模型协议

### Answer 模型

```yaml
answer:
  name: Qwen/Qwen3-30B-A3B-Instruct-2507
  service: local_vllm_generation
  temperature: 0.0
  max_input_tokens: 131072
  max_output_tokens: 16384
  thinking: default
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

### Judge 模型

```yaml
judge:
  name: deepseek-v4-flash
  service: api
  temperature: 0.0
  thinking: default
```

### Rerank 模型

```yaml
rerank:
  name: BAAI/bge-m3 or Qwen/Qwen3-Reranker-0.6B
  service: local_rerank_service
```

### 部署规划

```yaml
deployment:
  answer:
    model: Qwen/Qwen3-30B-A3B-Instruct-2507
    service: local_vllm_generation
    cuda_visible_devices: [0, 1, 2, 3]
    tensor_parallel_size: 4
    gpu_memory_utilization: 0.8
    max_model_len: 131072
    max_output_tokens: 16384

  embedding:
    model: Qwen/Qwen3-Embedding-0.6B
    service: local_vllm_embedding
    cuda_visible_devices: [4]
    gpu_memory_utilization: 0.4

  rerank:
    model: Qwen/Qwen3-Reranker-0.6B
    service: local_rerank_service
    cuda_visible_devices: [4]
    gpu_memory_utilization: 0.4
```

部署时默认 Answer LLM 独占 GPU 0-3，embedding 与 rerank 共享 GPU 4。`gpu_memory_utilization` 是服务启动时的目标显存占用上限；如果 rerank 后端不支持该参数，就合理限制一下。

## 2. Prompt Template 协议

### LoCoMo Judge Template

```text
Your task is to label an answer to a question as 'CORRECT' or 'WRONG'. You will be given the following data:
    (1) a question (posed by one user to another user),
    (2) a 'gold' (ground truth) answer,
    (3) a generated answer
which you will score as CORRECT/WRONG.

The point of the question is to ask about something one user should know about the other user based on their prior conversations.
The gold answer will usually be a concise and short answer that includes the referenced topic. The generated answer might be much longer, but you should be generous with your grading - as long as it touches on the same topic as the gold answer, it should be counted as CORRECT.

For time related questions, the gold answer will be a specific date, month, year, etc. The generated answer might be much longer or use relative time references, but you should be generous with your grading - as long as it refers to the same date or time period as the gold answer, it should be counted as CORRECT.

Now it's time for the real question:
Question: {question}
Gold answer: {gold_answer}
Generated answer: {generated_answer}

Return ONLY a valid JSON object in the following format:
{
  "label": "CORRECT"
}

The value of "label" must be exactly "CORRECT" or "WRONG". Do not include any explanation or extra text.
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
  accuracy

  f1

  bleu

  by_type:
    group_by: question_type_or_category
    fields: [accuracy, f1, bleu]

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
