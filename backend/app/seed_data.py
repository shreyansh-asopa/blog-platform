"""The sample authors and posts that `python -m app.seed` loads.

Each post's topics decide its cover: the seed uses the art drawn for its first topic
(app/seed_covers, made by scripts/draw_sample_art.py).
"""

from dataclasses import dataclass, field

AUTHORS = ["ada_writes", "grace_codes", "linus_notes", "maya_data", "arjun_ml", "sofia_secops"]


@dataclass
class SamplePost:
    author: str
    title: str
    content: str
    days_ago: int
    # Topic slugs, most relevant first
    topics: list[str]
    liked_by: list[str] = field(default_factory=list)
    # (commenter, text), oldest first
    comments: list[tuple[str, str]] = field(default_factory=list)


POSTS = [
    SamplePost(
        author="ada_writes",
        title="Welcome to Lumen",
        topics=["web-development", "software-engineering"],
        days_ago=0,
        liked_by=["grace_codes", "linus_notes"],
        comments=[
            ("grace_codes", "Congrats on the launch! The reading view is lovely."),
            ("linus_notes", "Dark mode by default, my eyes thank you."),
        ],
        content="""Lumen is a small, fast place to **write to think** and **publish to connect**.

## What you can do today

- Read posts from every author in one feed
- Like the ones that teach you something
- Join the discussion in the comments

## What's coming next

1. A Markdown editor with a live preview
2. Drafts, cover images and CSV export
3. Search across every post

> Good writing is clear thinking made visible.

Thanks for being one of the first readers.""",
    ),
    SamplePost(
        author="grace_codes",
        title="Async SQLAlchemy in five minutes",
        topics=["software-engineering", "data-engineering"],
        days_ago=1,
        liked_by=["ada_writes"],
        comments=[("ada_writes", "The table makes the case better than any paragraph could.")],
        content="""Async database access lets one worker serve **many requests**
while it waits on Postgres.

## The session

```python
async with sessionmaker() as session:
    session.add(post)
    await session.commit()
```

## Why bother?

| Mode  | Requests/s |
|-------|-----------:|
| sync  |        900 |
| async |       2400 |

The numbers are illustrative; measure your own app before you optimise.

Read more in [the SQLAlchemy docs](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html).""",
    ),
    SamplePost(
        author="linus_notes",
        title="Writing Git commit messages people can read",
        topics=["software-engineering"],
        days_ago=2,
        liked_by=["ada_writes", "grace_codes"],
        comments=[
            ("grace_codes", "The 50/72 rule changed my life."),
            ("ada_writes", "Saving this for the next code review."),
            ("linus_notes", "Glad it helps! Imperative mood is the hardest habit to build."),
        ],
        content="""A commit message is a letter to the next person who runs `git blame`, often you.

## The shape

```text
Add rate limiting to the login endpoint

Five attempts per minute per IP and username. Stops password
guessing without locking real users out for long.
```

## Three rules

- **Subject in the imperative:** "Add", not "Added"
- **Keep it under ~50 characters**, wrap the body at 72
- **Explain why**, the diff already shows what

That's it. Small habit, big payoff.""",
    ),
    SamplePost(
        author="ada_writes",
        title="CSS variables make dark mode easy",
        topics=["web-development"],
        days_ago=4,
        liked_by=["linus_notes"],
        content="""Define your colours once as tokens, then swap them for dark mode.

```css
:root {
  --bg: #ffffff;
  --text: #1a1a1a;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0f1115;
    --text: #e6e6e6;
  }
}

body {
  background: var(--bg);
  color: var(--text);
}
```

Every component reads `var(--bg)`, so none of them needs to know which theme is active.""",
    ),
    SamplePost(
        author="grace_codes",
        title="Optimistic updates with TanStack Query",
        topics=["web-development"],
        days_ago=6,
        liked_by=["ada_writes", "linus_notes"],
        comments=[("linus_notes", "The rollback part is what most tutorials skip. Nice.")],
        content="""When someone taps **Like**, show the heart straight away
and talk to the server afterwards.

## The recipe

1. `onMutate`: cancel queries in flight, save the old data, write the new data
2. `onError`: put the old data back
3. `onSettled`: refetch so the cache matches the server

```ts
onMutate: async () => {
  await queryClient.cancelQueries({ queryKey })
  const previous = queryClient.getQueryData(queryKey)
  queryClient.setQueryData(queryKey, (post) => ({ ...post, liked_by_me: true }))
  return { previous }
}
```

The app feels instant, and it stays correct when the network fails.""",
    ),
    SamplePost(
        author="linus_notes",
        title="Why your API errors deserve a schema",
        topics=["web-development", "software-engineering"],
        days_ago=9,
        liked_by=["grace_codes"],
        content="""Every error from the API should look the same:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Some fields are invalid",
    "request_id": "7f3c…",
    "details": [{ "field": "email", "message": "Not a valid email" }]
  }
}
```

- `code` is for **programs**: the frontend switches on it
- `message` is for **people**
- `request_id` lets support find the exact log line

One shape means one error component in the frontend, not twenty.""",
    ),
    SamplePost(
        author="ada_writes",
        title="Notes on learning in public",
        topics=["software-engineering"],
        days_ago=13,
        liked_by=["grace_codes", "linus_notes"],
        comments=[("grace_codes", "Point three is the one I needed to hear.")],
        content="""Some things I've learned from writing about what I'm learning:

1. **You understand it better** once you've explained it
2. **Mistakes get corrected fast**: readers are generous
3. **Nobody expects perfection**, only honesty
4. **Your future self** is your most grateful reader

Start small. One paragraph about one thing you figured out today is enough.""",
    ),
    # --- AI ---
    SamplePost(
        author="arjun_ml",
        title="What an AI agent actually is",
        days_ago=0,
        topics=["ai", "genai"],
        liked_by=["ada_writes", "grace_codes", "maya_data", "sofia_secops"],
        comments=[
            ("maya_data", "The loop diagram finally made it click for me."),
            (
                "linus_notes",
                "Point about budgets is underrated. Agents without limits get expensive.",
            ),
        ],
        content=""""Agent" is the most stretched word in tech right now. Strip away the hype and
an agent is a **loop**: a model that can decide what to do next, do it, look at the
result, and decide again.

## The loop

```text
goal ─▶ think ─▶ pick a tool ─▶ run it ─▶ observe ─┐
          ▲                                        │
          └────────────── not done yet ◀───────────┘
```

A chatbot answers once. An agent keeps going until the goal is met or it gives up.

## The three parts

1. **A model** that reasons about the next step
2. **Tools** it can call: search, a database query, a code runner, an API
3. **Memory** of what it has tried, so it doesn't repeat itself

## What makes one good

- **Narrow tools with clear names.** `get_invoice(id)` beats `run_sql(query)`
- **A budget:** a maximum number of steps and a spending limit
- **A human checkpoint** before anything irreversible, like sending an email

> An agent is only as trustworthy as the worst tool you hand it.

Start with one tool and one job. Add autonomy only when the simple version works.""",
    ),
    SamplePost(
        author="ada_writes",
        title="A plain-English guide to embeddings",
        days_ago=5,
        topics=["ai", "machine-learning"],
        liked_by=["arjun_ml", "grace_codes"],
        comments=[("arjun_ml", "The map analogy is the one I use with new team members too.")],
        content="""An embedding turns something messy, like a sentence, into a list of numbers
that captures its **meaning**.

## A map of meaning

Imagine a map where every word has a spot. "Cat" sits near "kitten", far from "invoice".
An embedding is that map, but with hundreds of dimensions instead of two.

```python
embed("How do I reset my password?")   # [0.12, -0.83, 0.44, ...]
embed("I forgot my login details")      # [0.10, -0.79, 0.47, ...]  close!
embed("Best pizza in Naples")           # [-0.65, 0.21, -0.09, ...] far away
```

## Why it matters

- **Search by meaning:** find "forgot my login" when someone types "reset password"
- **Grouping:** cluster support tickets without writing rules
- **Recommendations:** "readers of this post also liked…"

## Measuring closeness

The usual measure is **cosine similarity**: how much two vectors point the same way.
1 means the same direction, 0 means unrelated.

Embeddings are the quiet workhorse behind most "AI search" features you use every day.""",
    ),
    # --- Generative AI ---
    SamplePost(
        author="arjun_ml",
        title="RAG from scratch: retrieval before generation",
        days_ago=1,
        topics=["genai", "data-engineering"],
        liked_by=["maya_data", "ada_writes", "linus_notes"],
        comments=[
            ("maya_data", "Chunking is 80% of the work, can confirm."),
            ("ada_writes", "Loved the bit about citing sources. Trust is the whole game."),
        ],
        content="""Large language models know a lot, but not **your** documents. Retrieval-augmented
generation (RAG) fixes that: fetch the relevant facts first, then ask the model to answer
using only those.

## The pipeline

1. **Chunk** your documents into passages of a few hundred words
2. **Embed** each chunk and store the vectors (Postgres with `pgvector` works fine)
3. At question time, **embed the question** and fetch the closest chunks
4. **Prompt** the model with the question plus those chunks

```text
Answer using only the context below. If the answer isn't there, say so.

Context:
{top_5_chunks}

Question: {question}
```

## Where it goes wrong

| Problem | Fix |
| --- | --- |
| Chunks cut sentences in half | Split on headings and paragraphs |
| The right chunk ranks 8th | Retrieve 20, re-rank, keep 5 |
| Confident wrong answers | Ask for citations, check them |

RAG is mostly a **data engineering** problem wearing an AI costume. Get retrieval right
and the generation part is easy.""",
    ),
    SamplePost(
        author="grace_codes",
        title="Prompting is programming: patterns that hold up",
        days_ago=3,
        topics=["genai"],
        liked_by=["arjun_ml", "linus_notes"],
        comments=[("arjun_ml", "Examples over adjectives, every single time.")],
        content="""A prompt is a program written in English. The same habits that make code
reliable make prompts reliable.

## Be specific about the output

Bad: *"Summarise this."*
Better: *"Summarise this in three bullet points, each under 15 words, for a busy manager."*

## Show, don't describe

One good example beats a paragraph of adjectives:

```text
Turn the review into JSON.

Review: "Fast delivery, but the box was crushed."
{"sentiment": "mixed", "topics": ["delivery", "packaging"]}

Review: "{review}"
```

## Give it room to think

For anything with steps, ask the model to **work through the problem before answering**.
Accuracy on multi-step questions goes up noticeably.

## Version your prompts

Keep prompts in files, next to the code that uses them, with tests. A prompt change is a
behaviour change: it deserves a review like any other.""",
    ),
    SamplePost(
        author="linus_notes",
        title="Evaluating LLM features before you ship them",
        days_ago=8,
        topics=["genai", "software-engineering"],
        liked_by=["grace_codes", "arjun_ml", "sofia_secops"],
        comments=[("grace_codes", "Golden sets are just unit tests with better PR.")],
        content=""""It looked good when I tried it" is not a test plan. Language models are
non-deterministic, so they need **evaluation**, not just testing.

## Build a golden set

Collect 50 to 200 real inputs with the answer you'd accept. Include the awkward ones:
empty input, other languages, people trying to break it.

## Score automatically

- **Exact checks** where you can: valid JSON, required fields, length limits
- **A rubric** for the rest: correct, complete, polite, grounded in the source
- **A second model as grader**, spot-checked by a human every week

## Run it on every change

```bash
$ make eval
accuracy      0.91  (was 0.88)
format_valid  1.00
refusals      0.02
p95 latency   1.8s
```

Treat a drop in the score like a failing test: nothing merges until it's understood.

The teams shipping great AI features aren't the ones with the best prompts. They're the
ones who **measure**.""",
    ),
    # --- Machine learning ---
    SamplePost(
        author="arjun_ml",
        title="Why your validation score lies",
        days_ago=6,
        topics=["machine-learning"],
        liked_by=["maya_data"],
        comments=[
            ("maya_data", "Time-based splits saved one of our churn models. Great write-up.")
        ],
        content="""Your model scored 97% on validation and 71% in production. What happened?
Almost always: **leakage**, information from the future sneaking into training.

## Classic leaks

- **Random splits on time-series data.** Training on Tuesday to predict Monday is cheating
- **Duplicates across splits.** The same customer appears in train and test
- **Features computed on the whole dataset**, like scaling with the global mean

## Split like production

If the model will predict next month from past months, validate the same way:

```python
train = df[df.date < "2026-06-01"]
valid = df[(df.date >= "2026-06-01") & (df.date < "2026-07-01")]
```

## Sanity checks

1. Does a **dumb baseline** (predict the average) score far lower? If not, suspicious
2. Is one feature **too good to be true**? It probably is
3. Does performance hold on the **latest** data?

A lower, honest score beats a high one that collapses the day you deploy.""",
    ),
    SamplePost(
        author="maya_data",
        title="Feature stores without the hype",
        days_ago=11,
        topics=["machine-learning", "data-engineering"],
        liked_by=["arjun_ml", "grace_codes"],
        content="""A feature store solves one annoying problem: the feature your model trained on
must be computed **exactly the same way** when the model runs live.

## The problem

The data scientist computes `orders_last_30_days` in a notebook with pandas. The backend
team re-implements it in Java for serving. They disagree on time zones. The model quietly
gets worse.

## What a feature store gives you

- **One definition** of each feature, used for training and serving
- **Point-in-time lookups:** "what was this value on 3 March?" for leak-free training data
- **Fast reads** for live predictions

## Do you need one?

| Situation | Answer |
| --- | --- |
| One model, batch predictions | No: a well-named SQL view is enough |
| Several models sharing features | Probably |
| Real-time predictions under 50 ms | Yes |

Start with a shared SQL view and good tests. Graduate to a feature store when the pain
is real.""",
    ),
    # --- Data engineering ---
    SamplePost(
        author="maya_data",
        title="Batch vs streaming: choosing honestly",
        days_ago=2,
        topics=["data-engineering"],
        liked_by=["arjun_ml", "linus_notes", "sofia_secops"],
        comments=[
            ("linus_notes", "'Who acts on it, and how fast?' is going on a sticky note."),
            ("arjun_ml", "Micro-batches have saved us so much operational pain."),
        ],
        content="""Streaming sounds modern, batch sounds old. But the right question isn't
"which is better?" It's **"who acts on this data, and how fast?"**

## Ask how fresh it must be

| Use case | Freshness needed | Pick |
| --- | --- | --- |
| Monthly finance report | a day | batch |
| Product dashboard | an hour | micro-batch |
| Fraud check on a payment | under a second | streaming |

## The real cost of streaming

- **State:** joins and windows need storage that survives restarts
- **Late data:** events arrive out of order, so you need watermarks
- **On-call:** a pipeline that never stops can break at 3 a.m.

## A middle path

Micro-batches every 5 to 15 minutes give "near real time" with batch simplicity. Many
teams that "need streaming" are happy here.

Choose the slowest option that still meets the need. Your future on-call self will
thank you.""",
    ),
    SamplePost(
        author="maya_data",
        title="Idempotent pipelines: run it twice, get it once",
        days_ago=7,
        topics=["data-engineering", "software-engineering"],
        liked_by=["grace_codes", "linus_notes"],
        comments=[("grace_codes", "Same idea as our PUT /like endpoint. Idempotency everywhere!")],
        content="""Every pipeline will be re-run: after a crash, a bug fix, a backfill. The
question is whether re-running **doubles your revenue numbers**.

## The rule

A job is **idempotent** when running it once or five times gives the same result.

## Overwrite, don't append

```sql
-- Fragile: every retry adds the day again
INSERT INTO daily_sales SELECT ...;

-- Idempotent: replace exactly one day's slice
DELETE FROM daily_sales WHERE day = '2026-09-26';
INSERT INTO daily_sales SELECT ... WHERE day = '2026-09-26';
```

Wrap both in one transaction, or use `MERGE` / `INSERT ... ON CONFLICT`.

## Partition by the run's input

Each run should own **one slice**, usually a date. Backfilling last March is then just
"run the job for each day in March".

## Deterministic keys

Generate IDs from the data (a hash of source ID plus date), not random UUIDs, so a
re-run produces the same rows.

Build pipelines you're not afraid to re-run, and incidents become boring.""",
    ),
    SamplePost(
        author="grace_codes",
        title="Postgres full-text search before you reach for Elasticsearch",
        days_ago=9,
        topics=["data-engineering", "web-development"],
        liked_by=["maya_data", "ada_writes"],
        comments=[("ada_writes", "This is exactly how search works on Lumen!")],
        content="""Search looks like it needs a separate system. For most apps, **Postgres already
has one built in**.

## A search column that maintains itself

```sql
ALTER TABLE posts ADD COLUMN search_vector tsvector
  GENERATED ALWAYS AS (
    setweight(to_tsvector('english', title), 'A') ||
    setweight(to_tsvector('english', content), 'B')
  ) STORED;

CREATE INDEX ON posts USING gin (search_vector);
```

## Query it like a search box

```sql
SELECT title FROM posts
WHERE search_vector @@ websearch_to_tsquery('english', '"dark mode" -css')
ORDER BY ts_rank(search_vector, websearch_to_tsquery('english', '"dark mode" -css')) DESC;
```

You get stemming ("running" matches "run"), phrases, exclusions and ranking.

## When to move on

Typo tolerance, many languages or millions of documents with facets: that's when a
dedicated engine earns its operational cost. Until then, one database is simpler.""",
    ),
    # --- Software engineering ---
    SamplePost(
        author="linus_notes",
        title="Code review that makes people better",
        days_ago=4,
        topics=["software-engineering"],
        liked_by=["ada_writes", "grace_codes", "maya_data"],
        comments=[
            ("ada_writes", "Labelling nits as nits changed our team's review culture."),
            ("maya_data", "Reviewing in two passes is such a simple, good idea."),
        ],
        content="""A good review catches bugs. A great one leaves the author a better engineer.

## Two passes

1. **The big picture:** is this the right change? Right place? Right approach?
2. **The details:** naming, edge cases, tests

Don't polish variable names on a PR that should be redesigned.

## Label your comments

- **blocking:** must change before merge
- **suggestion:** I'd do this, your call
- **nit:** tiny, ignore if you like
- **question:** I'm curious, not criticising

## Ask, don't command

"What happens if `items` is empty?" teaches more than "handle empty items".

## Keep PRs small

Under 400 lines gets a real review. 2,000 lines gets "LGTM".

Praise what's good, too. People repeat what gets noticed.""",
    ),
    SamplePost(
        author="grace_codes",
        title="Tests that describe behaviour, not implementation",
        days_ago=12,
        topics=["software-engineering"],
        liked_by=["linus_notes"],
        content="""If renaming a private function breaks twenty tests, the tests are testing the
wrong thing.

## Test through the front door

```python
def test_a_draft_is_hidden_from_other_readers(client, ada, grace):
    post = create_post(client, ada)

    response = client.get(f"/posts/{post['slug']}", headers=grace.headers)

    assert response.status_code == 404
```

This test survives any refactor of the service, the repository or the SQL. It breaks
only if **behaviour** changes, which is exactly when you want to know.

## Name tests as sentences

`test_a_draft_is_hidden_from_other_readers` documents a rule of the system. Read the
test names and you know what the app promises.

## Mock at the edges only

Fake the email provider, the payment API, the clock. Keep your own code real.

Good tests make change **safe**, not slow.""",
    ),
    # --- Cloud & DevOps ---
    SamplePost(
        author="sofia_secops",
        title="Docker images: small, fast and boring",
        days_ago=3,
        topics=["cloud-devops"],
        liked_by=["linus_notes", "grace_codes"],
        comments=[("linus_notes", "Layer ordering alone cut our CI time in half.")],
        content="""A good container image is **small** (fast to pull), **fast** to build and
**boring**: nothing in it you didn't choose.

## Order layers by how often they change

```dockerfile
FROM python:3.13-slim
WORKDIR /app

# Dependencies change rarely: cached most builds
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Code changes every commit: only this layer rebuilds
COPY app ./app
```

## Keep it lean

- Start from a **slim** base image
- Add a `.dockerignore` so tests, caches and `.env` never get copied in
- Use **multi-stage builds** when you need compilers only at build time

## Run as a normal user

```dockerfile
RUN useradd --create-home app
USER app
```

If someone breaks in, they shouldn't be root.

Boring images are easy to scan, fast to ship and never surprising.""",
    ),
    SamplePost(
        author="sofia_secops",
        title="A CI pipeline you can trust",
        days_ago=10,
        topics=["cloud-devops", "software-engineering"],
        liked_by=["linus_notes", "maya_data"],
        content="""CI is only useful if a green check **means something**. Here's what ours checks
on every pull request.

## The jobs

1. **Lint and format:** style arguments settled by a machine
2. **Type check:** a whole class of bugs gone before tests run
3. **Migrations:** apply them to a real database, then check the models match
4. **Tests** against a real Postgres, not a mock
5. **Build the Docker image**, so "works on my machine" can't reach main

## Make it required

Branch protection turns CI from advice into a rule: no merge until every job passes,
admins included.

## Keep it fast

- Cache dependencies between runs
- Run independent jobs in parallel
- Aim for under five minutes, or people stop waiting for it

## Never flaky

A test that fails randomly trains everyone to ignore red. Fix it or delete it the same
day.""",
    ),
    # --- Security ---
    SamplePost(
        author="sofia_secops",
        title="Storing passwords in 2026: Argon2 and nothing else",
        days_ago=5,
        topics=["security"],
        liked_by=["ada_writes", "grace_codes", "linus_notes", "arjun_ml"],
        comments=[
            ("grace_codes", "The table of what not to use should be in every onboarding doc."),
            ("ada_writes", "Lumen uses Argon2 too, glad to see it recommended."),
        ],
        content="""If your database leaks tomorrow, what do attackers get? With the right
hashing: almost nothing useful.

## Never store passwords, store slow hashes

A password hash must be **slow on purpose**, so guessing billions of passwords takes
years, not minutes.

| Approach | Verdict |
| --- | --- |
| Plain text | never |
| MD5, SHA-256 | far too fast |
| bcrypt | OK for old systems |
| **Argon2id** | use this |

## In Python

```python
from pwdlib import PasswordHash

hasher = PasswordHash.recommended()   # Argon2id with sensible settings
stored = hasher.hash("correct horse battery staple")
hasher.verify("correct horse battery staple", stored)   # True
```

Each hash includes its own random **salt**, so identical passwords look different.

## The rest of the checklist

- Rate-limit login attempts
- Same error for "no such user" and "wrong password"
- Allow long passphrases; don't force odd symbol rules""",
    ),
    SamplePost(
        author="linus_notes",
        title="A security checklist for your next pull request",
        days_ago=14,
        topics=["security", "web-development"],
        liked_by=["sofia_secops", "ada_writes"],
        comments=[("sofia_secops", "Printing this for our team wall.")],
        content="""Most security bugs aren't clever hacks. They're small oversights in ordinary
pull requests. Five questions catch most of them.

## 1. Who is allowed to do this?

Check **authorisation** on the server for every request. Hiding a button is not security.

## 2. Is user input treated as data?

Use parameterised queries, never string-built SQL:

```python
# Dangerous
db.execute(f"SELECT * FROM users WHERE name = '{name}'")

# Safe
db.execute(select(User).where(User.name == name))
```

## 3. Could this leak something?

Error messages, logs and API responses shouldn't expose emails, tokens or stack traces.

## 4. Are uploads checked?

Verify the file's real type from its bytes, cap the size, and store it under a random
name.

## 5. Are secrets out of the code?

Keys belong in environment variables, never in the repository, especially a public one.

Ask these five on every PR and you'll prevent more incidents than any scanner.""",
    ),
]
