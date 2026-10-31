# Business case: Cymbal Travel ADK Agent Console

**Four Google ADK agent patterns for a travel business, in one local console.**

## Who buys this

The buyer is a digital or innovation lead at a travel company considering AI agents. The users are developers evaluating Google's Agent Development Kit ([ADK docs](https://google.github.io/adk-docs/)) and content teams checking travel copy.

## The problem and what it costs

Teams want to try agents, but many generative AI projects stall after the demo. Gartner predicted that at least 30% of generative AI projects would be abandoned after proof of concept by the end of 2025 ([Gartner, 2024](https://www.gartner.com/en/newsroom/press-releases/2024-07-29-gartner-predicts-30-percent-of-generative-ai-projects-will-be-abandoned-after-proof-of-concept-by-end-of-2025)). Seeing several agent patterns side by side, with honest offline behaviour, helps a team pick a pattern before it commits.

## How the repo solves it

| Need | What in the repo does it |
|---|---|
| Grounded answers | Travel Scout: an `LlmAgent` with the `google_search` tool |
| Structured output | Destination Verifier: an `LlmAgent` with an `output_schema` (`CountryCapital`) |
| Review and fix copy | Brochure Auditor: a `SequentialAgent` of a critic (search plus references) and a reviser |
| One console | A FastAPI backend over ADK's `InMemoryRunner` and a React console. It works offline with introspection and schema checks, and with Gemini or Vertex AI when credentials are set. |

## Use-case scenarios

All of these organisations are fictional.

1. **A tour operator's content team** runs brochure claims through the auditor to catch factual errors before printing.
2. **A travel agency's booking site** uses the structured-output pattern to validate destination data before it reaches a form.
3. **An internal AI team** uses the console to show stakeholders four patterns in one session.

## ROI: a worked model (illustrative)

These figures are **illustrative assumptions** unless a source is linked.

| Input | Value | Basis |
|---|---|---|
| Brochure pages checked a year | 400 | Assumption |
| Minutes of manual fact-checking per page | 20 | Assumption |
| Share of that time saved with the auditor | 40% | Assumption |
| Editor loaded cost an hour | US$50 | Assumption |

Saving: 400 × 20 min × 40% ≈ 53 hours, about **US$2,700 a year**. The bigger value is a faster, cheaper decision about which agent pattern to build.

## Path to production

1. Pick one pattern and one workflow, and measure it against current practice.
2. Replace `InMemoryRunner` with persistent sessions and add authentication.
3. Log every model call and its sources for review.

## Risks and limits

- The agents come from a Google lab and are examples, not products.
- Search-grounded answers can still be wrong, so keep a human check on anything published.
- All screenshots in the repo were taken without model credentials, so no output quality is shown.

**Case strength:** **Weak.** It is an honest learning console. The business case is about choosing a pattern, not about this code saving money.

## Sources

- Google, Agent Development Kit documentation: https://google.github.io/adk-docs/
- Gartner (2024), 30% of GenAI projects abandoned after proof of concept: https://www.gartner.com/en/newsroom/press-releases/2024-07-29-gartner-predicts-30-percent-of-generative-ai-projects-will-be-abandoned-after-proof-of-concept-by-end-of-2025
