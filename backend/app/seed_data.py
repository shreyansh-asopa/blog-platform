"""The sample authors and posts that `python -m app.seed` loads.

Each post's topics decide its cover: the seed uses the art drawn for its first topic
(app/seed_covers, made by scripts/draw_sample_art.py).
"""

from dataclasses import dataclass, field

AUTHORS = [
    "ada_writes",
    "grace_codes",
    "linus_notes",
    "maya_data",
    "arjun_ml",
    "sofia_secops",
    # Writing about life outside work
    "priya_travels",
    "tomas_cooks",
    "leah_reads",
    "omar_money",
]


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
2. Drafts, cover images and PDF or Word export
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
    # --- Life outside work ---
    SamplePost(
        author="leah_reads",
        title="The slow morning routine that fixed my week",
        topics=["lifestyle", "health-wellness"],
        days_ago=0,
        liked_by=["priya_travels", "omar_money", "ada_writes"],
        comments=[
            ("priya_travels", "The phone-in-the-kitchen rule is the hardest one and the best one."),
            ("ada_writes", "Trying the ten-minute walk tomorrow."),
        ],
        content="""For years my mornings started with my phone and ended with me running late.
Here is the small routine that changed that. None of it takes more than **45 minutes**.

## The four steps

1. **Water before coffee.** A full glass, first thing.
2. **Ten minutes outside.** A walk round the block, whatever the weather.
3. **One page in a notebook.** Not a journal: just what's on my mind.
4. **Coffee and one chapter** of whatever I'm reading.

## The rule that makes it work

The phone charges in the kitchen, not by the bed. I check it only after step four.

> You don't need a perfect morning. You need one that is yours before it's everyone else's.

Two months in, the biggest change isn't the extra time. It's that I start the day
having *chosen* something, instead of reacting to it.""",
    ),
    SamplePost(
        author="priya_travels",
        title="Packing light: one bag for two weeks",
        topics=["travel", "lifestyle"],
        days_ago=2,
        liked_by=["leah_reads", "tomas_cooks"],
        comments=[
            ("tomas_cooks", "Merino wool changed my life. No notes."),
            ("leah_reads", "Where does the book go though?"),
            ("priya_travels", "E-reader. It's the one gadget I never leave behind."),
        ],
        content="""I've travelled with a single 35-litre backpack for three years now:
Portugal, Japan, Peru. Here's the list, and the thinking behind it.

## The list

| Item | How many |
|------|---------:|
| T-shirts (merino) | 4 |
| Trousers | 2 |
| Light jumper | 1 |
| Rain jacket | 1 |
| Underwear and socks | 5 each |
| Shoes (worn, not packed) | 1 pair |

## Three rules

- **Everything goes with everything.** Pick two or three colours and stick to them.
- **Plan to do laundry.** A sink and a bar of soap every four days beats a second bag.
- **Pack for the trip you're taking**, not the one you're afraid of. Shops exist abroad.

The real win isn't the airline fees you save. It's stepping off a train and walking
straight into the city instead of hunting for a taxi.""",
    ),
    SamplePost(
        author="tomas_cooks",
        title="Five pantry staples that make weeknight dinners easy",
        topics=["food", "health-wellness"],
        days_ago=3,
        liked_by=["leah_reads", "omar_money", "maya_data"],
        comments=[("omar_money", "Also cheaper than takeaway. Win-win.")],
        content="""Most of my weeknight cooking takes 20 minutes, and it starts with what's
already in the cupboard. Keep these five in stock and dinner is never far away.

## The staples

1. **Tinned chickpeas.** Roast them, mash them, toss them in a curry.
2. **Good olive oil.** The single ingredient that most improves simple food.
3. **Dried pasta.** Pair with garlic, chilli and oil for a meal in ten minutes.
4. **Tinned tomatoes.** The base of a hundred sauces and soups.
5. **Lemons.** A squeeze at the end wakes up almost anything.

## A 15-minute example

Warm oil with sliced garlic and chilli, add a drained tin of chickpeas and a tin of
tomatoes, simmer for ten minutes, finish with lemon and black pepper. Serve with bread.

> Cooking every night is easier when you stop starting from zero.""",
    ),
    SamplePost(
        author="omar_money",
        title="The 50/30/20 budget, explained simply",
        topics=["personal-finance"],
        days_ago=4,
        liked_by=["priya_travels", "leah_reads", "grace_codes", "linus_notes"],
        comments=[
            ("grace_codes", "Finally a budget I can remember without a spreadsheet."),
            ("priya_travels", "Travel falls under wants, I assume? 😅"),
            ("omar_money", "It does. Which is exactly why it's worth planning for."),
        ],
        content="""Budgeting doesn't have to mean tracking every coffee. The **50/30/20 rule**
splits your take-home pay into three buckets.

## The three buckets

| Bucket | Share | Examples |
|--------|------:|----------|
| Needs | 50% | Rent, bills, groceries, transport |
| Wants | 30% | Eating out, hobbies, holidays |
| Savings | 20% | Emergency fund, pension, paying off debt |

## Making it automatic

- On payday, move the **20% out first**, before you can spend it.
- Keep wants in a separate account, so "can I afford this?" is one glance.
- Review once a month, not once a day.

## When it doesn't fit

In an expensive city, needs can be 60% or more. That's fine: treat the numbers as a
starting point, and shrink wants before savings.

*This is general information, not financial advice.*""",
    ),
    SamplePost(
        author="leah_reads",
        title="How I read 40 books a year without speed reading",
        topics=["books", "lifestyle"],
        days_ago=5,
        liked_by=["tomas_cooks", "ada_writes", "priya_travels"],
        comments=[
            ("ada_writes", "Permission to quit a book is so freeing."),
            ("tomas_cooks", "Audiobooks while cooking count, right?"),
            ("leah_reads", "Absolutely. A story is a story."),
        ],
        content="""Forty books sounds like a lot. It works out to about **20 pages a day**.
Here's how that fits into an ordinary week.

## What actually helped

- **Always carry a book.** Queues, trains and waiting rooms add up.
- **Quit books you don't enjoy.** Fifty pages is enough to decide.
- **Read two at once:** one easy, one demanding. Pick by mood.
- **Replace one scroll a day.** The evening scroll became my reading time.

## What didn't help

Challenges and streak apps. They made reading feel like homework, and I read
*worse* books just to hit a number.

> The goal isn't to finish more books. It's to spend more of your life inside good ones.""",
    ),
    SamplePost(
        author="priya_travels",
        title="Three days in Lisbon on a small budget",
        topics=["travel", "food"],
        days_ago=6,
        liked_by=["tomas_cooks", "omar_money"],
        comments=[
            ("tomas_cooks", "The custard tarts at Belém are worth the queue. Every time."),
            ("omar_money", "Love a trip with a real budget attached."),
        ],
        content="""Lisbon is hilly, sunny and still kinder to your wallet than most European
capitals. Here's a relaxed three-day plan.

## Day 1: Alfama and the castle

Wander the old streets with no map, then climb to the castle for the view at sunset.

## Day 2: Belém

Take the tram west for the monastery, the tower, and *pastéis de nata* straight from
the oven.

## Day 3: A day trip to Sintra

A 40-minute train ride to palaces in the forest. Go early; it gets busy by eleven.

## Rough costs per day

| Item | Cost |
|------|-----:|
| Hostel or guesthouse | €35 |
| Food | €25 |
| Transport pass | €7 |
| Sights | €15 |

Walk more than you think you can: the best parts of the city are between the sights.""",
    ),
    SamplePost(
        author="omar_money",
        title="Building an emergency fund, one small step at a time",
        topics=["personal-finance", "lifestyle"],
        days_ago=7,
        liked_by=["leah_reads", "sofia_secops"],
        comments=[("sofia_secops", "Automate it and forget it. Same rule as backups.")],
        content="""An emergency fund is money set aside for the surprises: a broken boiler,
a vet bill, a gap between jobs. It's the difference between a bad week and a crisis.

## How much?

Aim for **three to six months** of essential spending. If that sounds impossible,
start with a smaller goal: one month, or even a fixed amount like 500.

## How to build it

1. Open a **separate savings account**, so it's out of sight.
2. Set up a **standing order** for payday, however small.
3. Put windfalls in: tax refunds, birthday money, a bonus.
4. **Refill it** after you use it. That's what it's for.

> The best time to build an emergency fund is before you need it.
> The second best time is today.

*General information only, not personal financial advice.*""",
    ),
    SamplePost(
        author="tomas_cooks",
        title="Sourdough for beginners: what I wish I'd known",
        topics=["food"],
        days_ago=8,
        liked_by=["leah_reads", "priya_travels", "arjun_ml"],
        comments=[
            ("arjun_ml", "Weighing everything is the tip that finally made mine work."),
            ("tomas_cooks", "Bakers and engineers agree: measure, don't guess."),
        ],
        content="""My first five loaves were bricks. The sixth was bread. Here's what changed.

## The lessons

- **Your starter needs to be lively.** It should double within 4–8 hours of feeding.
- **Weigh everything.** Cups vary; grams don't.
- **Watch the dough, not the clock.** A warm kitchen ferments twice as fast as a cold one.
- **Bake hotter than feels right.** A lidded pot at 240 °C gives the crust.

## A simple ratio

| Ingredient | Amount |
|------------|-------:|
| Bread flour | 500 g |
| Water | 350 g |
| Starter | 100 g |
| Salt | 10 g |

Mix, fold every 30 minutes for two hours, shape, rest in the fridge overnight, bake.

Your first loaf won't be perfect. Eat it anyway. It will still be better than shop bread.""",
    ),
    SamplePost(
        author="leah_reads",
        title="Ten novels to read on a long journey",
        topics=["books", "travel"],
        days_ago=9,
        liked_by=["priya_travels", "tomas_cooks", "linus_notes"],
        comments=[
            ("priya_travels", "Adding three of these for my next flight."),
            ("linus_notes", "The Remains of the Day on a train is perfect."),
        ],
        content="""A long train or flight is the best reading time there is. These are
novels that pull you in and hold you for hours.

## The list

1. *The Remains of the Day*, Kazuo Ishiguro
2. *A Gentleman in Moscow*, Amor Towles
3. *The Shadow of the Wind*, Carlos Ruiz Zafón
4. *Pachinko*, Min Jin Lee
5. *Circe*, Madeline Miller
6. *The Night Circus*, Erin Morgenstern
7. *Station Eleven*, Emily St. John Mandel
8. *Life of Pi*, Yann Martel
9. *The Name of the Wind*, Patrick Rothfuss
10. *Anxious People*, Fredrik Backman

## How I chose

Each one is **easy to start** and **hard to put down**, and none needs a pencil and
notes. Save the demanding books for home.""",
    ),
    SamplePost(
        author="omar_money",
        title="Walking 8,000 steps a day: what changed after 90 days",
        topics=["health-wellness", "lifestyle"],
        days_ago=11,
        liked_by=["leah_reads", "priya_travels", "maya_data"],
        comments=[
            ("maya_data", "Do you have the step data? I'd love to see the chart."),
            ("omar_money", "Ha, of course. Maybe a follow-up post."),
        ],
        content="""I work at a desk all day. In January I set one goal: **8,000 steps**, every
day, for three months. No gym, no diet.

## What changed

- **Sleep.** I fall asleep faster, and wake up less in the night.
- **Mood.** The afternoon slump mostly disappeared.
- **Thinking.** Some of my best ideas now arrive on the walk home.

## How I fitted it in

- Phone calls became walking calls.
- I got off the bus one stop early.
- A 15-minute walk after lunch, every day.

## What didn't change

I didn't lose much weight, and that's fine. It was never really about that.

*I'm not a doctor. If you have health conditions, check with one before starting a new routine.*""",
    ),
    SamplePost(
        author="tomas_cooks",
        title="Eating well on a busy week: a simple meal prep plan",
        topics=["health-wellness", "food"],
        days_ago=12,
        liked_by=["omar_money", "grace_codes"],
        comments=[("grace_codes", "Sunday prep has saved my weekday lunches.")],
        content="""Two hours on Sunday gives me healthy lunches all week. The trick is to
prepare **components**, not whole meals, so nothing gets boring.

## Sunday: prepare

- A tray of **roasted vegetables**
- A pot of **grains**: rice, quinoa or farro
- A **protein**: baked tofu, chicken or boiled eggs
- One **sauce**: tahini-lemon, pesto or a yoghurt dressing

## Weekdays: combine

| Day | Bowl |
|-----|------|
| Mon | Grains, vegetables, eggs, tahini |
| Tue | Vegetables in a wrap with pesto |
| Wed | Grains, tofu, yoghurt dressing |
| Thu | Leftovers turned into a soup |
| Fri | Treat yourself: eat out |

Store everything in glass boxes, and most of it keeps for four days in the fridge.""",
    ),
    SamplePost(
        author="priya_travels",
        title="Books that made me want to travel",
        topics=["books", "travel"],
        days_ago=13,
        liked_by=["leah_reads", "omar_money"],
        comments=[
            ("leah_reads", "Adding The Great Railway Bazaar to my list right now."),
            ("priya_travels", "It's the reason I took the night train through Vietnam."),
        ],
        content="""Some books make you want to pack a bag the moment you close them.
These did that for me.

## The shelf

- ***The Great Railway Bazaar*** by Paul Theroux. Across Asia by train, grumpy and brilliant.
- ***A Walk in the Woods*** by Bill Bryson. Funny, warm, and about the joy of being lost.
- ***In Patagonia*** by Bruce Chatwin. Short chapters, strange stories, the end of the world.
- ***Wild*** by Cheryl Strayed. Grief, and 1,100 miles on foot.

## What they share

None of them is really about the destination. They're about the **change in the
traveller**, and that's the part of travel that stays with you.

> Not all those who wander are lost. *(J. R. R. Tolkien)*""",
    ),
]
