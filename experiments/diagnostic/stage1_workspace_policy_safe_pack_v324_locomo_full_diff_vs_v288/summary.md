# stage1_workspace_policy_safe_pack_v324_locomo_full_diff_vs_v288

## Purpose

Verify whether v324 can replace v288 on LoCoMo non-adversarial full after moving selected-context pack limits to build-owned `memory_workspace_policy_v1`.

## Diff

| Item | Result |
|---|---:|
| Samples | `1540` |
| Prompt diff | `1537/1540` |
| Answer diff | `691/1540` |
| Evidence full diff | `1537/1540` |
| Retrieval hit order diff | `1/1540` |
| Route diff | `0/1540` |
| Avg query tokens | `6093.962337662338 -> 5547.798051948052` |
| Avg context chars | `17401.47857142857 -> 15794.304545454546` |

V324 reduces LoCoMo avg query tokens by about `546` tokens/sample and brings the average below the 6K target. The large prompt/evidence diff is expected because selected context applies to `1537/1540` LoCoMo samples.

## Diagnosis

The token reduction is too aggressive for LoCoMo. The build-owned selected-context policy packs avg `3.99` selected rows versus v288's avg `5.55`; this saves tokens but changes many answers and loses more judged correct answers than it gains.

Next algorithm step should keep policy ownership but relax selected-context pack limits, for example increasing rows/window/chars before considering any LTS promotion.
