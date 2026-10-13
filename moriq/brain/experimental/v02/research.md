# Local model research — 2026-10-12

The host reports an AMD Ryzen 7 5700U, 15.4 GiB RAM, and CPU inference. Ollama
discovered integrated Radeon graphics but did not select it; no GPU workaround
was applied. Docker's roughly 7.44 GiB allowance is not the host model's memory
budget: Ollama runs on Windows and shares physical memory with Docker and other
applications. Existing tags and application settings must be preserved.

| Candidate | Published/observed Windows artifact | License | Experiment rationale |
| --- | --- | --- | --- |
| Qwen3 4B | Existing 2.50 GB Q4_K_M; approximately 3.18 GB loaded at context 4096 | Apache 2.0 | Baseline; test prompt change without another download. |
| Qwen3 4B Instruct-2507 | Separate instruct tag; not downloaded | Apache 2.0 | Direct next comparison for the installed thinking-only variant; no measured result here. |
| Qwen3.5 2B | Downloaded 2.68 GB Q8_0 package including vision projector; approximately 2.36 GB loaded for text at context 4096 | Apache 2.0 | Smaller parameter count and supported non-thinking request; test quality rather than assume it improves. |
| Qwen3.5 4B | Published llama.cpp variant approximately 3.3 GB Q4_K_M | Apache 2.0 | Potential later capacity comparison; not yet measured here. |
| Gemma 3 4B | Published approximately 3.4 GB Q4_K_M package with vision projector | Gemma terms | Plausible alternative within host RAM, but extra download and different terms; no measured quality claim. |
| Qwen2.5 3B | Published approximately 1.9 GB Q4_K_M | Qwen Research License | Compact alternative; its license is not Apache 2.0. No measured quality claim or production-use recommendation. |

Sizes are approximate download/package sizes, not peak runtime memory. Ollama's
model pages can show both MLX and llama.cpp artifacts; this Windows experiment
uses the actual downloaded GGUF tag and digest, not the MLX size. Context caches,
runner overhead and other applications also require RAM. No paid account/API
was used. Only Qwen3.5 2B was added; existing tags were retained.

Primary sources checked October 12:

- [Qwen3 4B artifact](https://ollama.com/library/qwen3:4b)
- [Qwen3.5 2B artifact](https://ollama.com/library/qwen3.5:2b)
- [Qwen3.5 4B artifact](https://ollama.com/library/qwen3.5:4b)
- [Gemma 3 4B artifact and terms](https://ollama.com/library/gemma3:4b)
- [Qwen2.5 3B artifact and license](https://ollama.com/library/qwen2.5:3b)
- [Qwen thinking and sampling guidance](https://qwen.readthedocs.io/en/stable/getting_started/quickstart.html)

## Thinking diagnosis

The installed Qwen3 template ends the last user message with an open `<think>`
block unconditionally. The prior `think:false` probe exposed reasoning in the
answer rather than providing a reliable final-only response. The installed
metadata identifies `general.finetune=Thinking`, `general.version=2507`, and links
the Qwen3-4B-Thinking-2507 license. Its digest matches the Ollama `4b-thinking` tag.
The [official model card](https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507)
explicitly supports only thinking mode. This establishes a variant mismatch in
the earlier non-thinking assumption, not a defect requiring a template hack.
The template was captured without modifying the installed tag.

Qwen's original hybrid-model documentation describes `/no_think` and
`enable_thinking=False`; that guidance does **not** apply to this thinking-only
2507 variant. The initial soft-switch screen still
spent substantial time thinking, and V0.2's concise case consumed all 1,500 tokens
without a final answer. Thus the switch cannot be assumed effective for this
installed artifact. The existing `soft` profile names are retained to preserve
the exact experiment, but are not evidence of non-thinking operation. The
[separate Qwen3 4B instruct tag](https://ollama.com/library/qwen3:4b-instruct)
is a more appropriate next mode comparison; it has not been tested or installed.
Qwen3.5 is tested separately with the Ollama API's
`think:false`, and actual returned thinking/delivery are measured.

V0.1's permission to offer general examples and its broad teaching checklist
may encourage continuation after a correct evidence-gap statement. This is an
inference, tested by the shorter prompt; it is not an established sole cause.
Small-model capacity, template behavior, sampling and output limits can all
contribute. Removing thinking can improve delivery while leaving factual errors
intact. No upstream application change is justified by these observations.
