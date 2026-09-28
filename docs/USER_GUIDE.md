# Lumen user guide

This guide takes you from nothing installed to writing and publishing posts. No previous
experience with Docker, Python or React is needed: copy the commands exactly as shown.

## Contents

1. [What you need](#1-what-you-need)
2. [Get the code](#2-get-the-code)
3. [Configure](#3-configure)
4. [Start Lumen](#4-start-lumen)
5. [Create your account](#5-create-your-account)
6. [Reading and finding posts](#6-reading-and-finding-posts)
7. [Writing a post](#7-writing-a-post)
8. [Check your writing](#8-check-your-writing)
9. [Managing your posts](#9-managing-your-posts)
10. [Likes and comments](#10-likes-and-comments)
11. [Admin tools](#11-admin-tools)
12. [Themes and phones](#12-themes-and-phones)
13. [Stopping, restarting and resetting](#13-stopping-restarting-and-resetting)
14. [Common problems](#14-common-problems)

## 1. What you need

| Tool | Why | Get it |
|---|---|---|
| **Docker Desktop** | Runs the database and the API in containers, so you don't install Python or PostgreSQL yourself | https://www.docker.com/products/docker-desktop/ |
| **Node.js 24** (includes `npm`) | Runs the website while you use it | https://nodejs.org/ |
| **Git** | Downloads the code | https://git-scm.com/ (already on most Macs) |
| A terminal | To type the commands | Terminal on macOS, PowerShell or Git Bash on Windows |

Check they are installed (each should print a version):

```sh
docker --version
node --version    # v24.x
git --version
```

Start **Docker Desktop** and wait until it says it is running before continuing.

## 2. Get the code

```sh
git clone https://github.com/shreyansh-asopa/blog-platform.git
cd blog-platform
```

Every command below is run from this `blog-platform` folder unless it says otherwise.

## 3. Configure

Lumen reads its settings from a file called `.env`. Make one from the example:

```sh
cp .env.example .env
```

Open `.env` in any text editor and set two values:

1. `POSTGRES_PASSWORD`: replace `change-me` with a password of your choice for the local
   database.
2. `JWT_SECRET`: a long random string that signs login tokens (at least 32 characters).
   Generate one with:

   ```sh
   openssl rand -hex 32
   ```

   and paste the output after `JWT_SECRET=`.

`.env` is private: it is git-ignored, so it is never committed. Don't share it.

**Optional: turn on the AI writing checks.** Grammar checking works without any key. The
AI parts (whole-sentence fixes, Tone, and "Simplify with AI") need one free key:

- Google Gemini: create a key at https://aistudio.google.com/apikey and add
  `GEMINI_API_KEY=your-key` to `.env`, or
- Groq: create a key at https://console.groq.com/keys and add `GROQ_API_KEY=your-key`.

If both are set, Gemini is used first and Groq takes over when Gemini is busy or out of quota. You can add a key later; see
[Turning on AI later](#turning-on-ai-later).

## 4. Start Lumen

**The database and API:**

```sh
docker compose up -d --build
```

The first time, this downloads and builds everything (a minute or two). It starts two
containers: `blog-db` (PostgreSQL) and `blog-api` (the API). The API sets up the database
tables by itself.

Check it is ready:

```sh
curl localhost:8000/ready
```

Expected: `{"status":"ok","database":"up"}`. If you get an error, wait a few seconds and
try again.

**Sample content (optional but recommended):**

```sh
docker compose exec api python -m app.seed
```

This adds 10 example authors and 35 posts with likes and comments, so the site isn't
empty. Running it again never adds anything twice. It prints the sample authors' passwords once; you
don't need them to use the site.

**The website** (in a new terminal window, so it can keep running):

```sh
cd frontend
npm install     # first time only
npm run dev
```

Open **http://localhost:5173** in your browser. You should see the Lumen home page with a
welcome block and the latest posts. Leave this terminal open while you use Lumen; press
`Ctrl+C` in it to stop the website.

## 5. Create your account

1. Click **Create account** at the bottom of the sidebar.
2. Enter an email, a username (3–50 letters, digits or `_`) and a password (8–128
   characters).
3. Click **Create account**. You are logged in straight away and taken to the home page.

Next time, click **Log in** and use your username **or** email with your password. For
security, a login lasts 30 minutes; after that you are logged out and simply log in again.

### Making yourself an admin (optional)

Admins can change other users' roles, see the audit log, and edit or delete any post or
comment. The first admin has to be made by hand. Replace `you` with your username:

```sh
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

At the `blog=#` prompt type:

```sql
UPDATE users SET role = 'admin' WHERE username = 'you';
```

It should answer `UPDATE 1`. Type `\q` to leave. Refresh the browser: an **Admin** link
appears in the sidebar. After that, admins can promote others from the Admin page.

## 6. Reading and finding posts

- **Feed** (home): the latest published posts, newest first, 20 per page. Beside it,
  **Trending posts** shows the most liked and discussed posts of the last 7 days.
- **Trending topics** in the sidebar lists this week's most active topics. **More** opens a
  picker with all 14 topics. Clicking a topic opens its page (`/t/<topic>`).
- **Post page:** click any post to read it. Click the author's name to see their profile
  and all their posts (`/u/<username>`).
- **Search:** click **Search** in the sidebar, type in **Search posts…**, and optionally
  pick a **Topic**. Results are ordered by best match, and titles count more than body text.
  You can use:
  - `"exact phrase"` in quotes
  - `python OR rust` for either word
  - `-word` to leave out posts containing a word

## 7. Writing a post

Click **Write** in the sidebar (you must be logged in).

1. **Title:** type it in **Post title…** (up to 200 characters).
2. **Body:** type in **Write your post here…**. The toolbar above it offers:
   - **Text style:** Paragraph, Heading, Subheading
   - **Font:** Sans, Serif, Mono; **Size:** Small, Normal, Large, Extra large
   - Bold, Italic, Underline, Strikethrough, text colour, alignment (left, centre, right,
     justify)
   - Bulleted and numbered lists, Quote, Code block, Link
   - Undo, Redo, and Clear formatting

   Tables in existing posts are shown and can be edited, but the toolbar has no button to
   insert a new one.
3. **Topics:** choose up to 3 so readers can find the post.
4. **Save draft** (or press `Ctrl+S`, `⌘+S` on a Mac). A new post is always saved as a
   draft first; only you (and admins) can see drafts.
5. **Cover image:** after the first save, add a cover (JPEG, PNG or WebP, up to 5 MB).
   Before saving, the editor shows "Save a draft first, then add a cover."
6. **Publish** makes the post public. Its web address (slug) is fixed from then on, so
   links you share keep working even if you change the title.

If you try to leave with unsaved changes, Lumen asks **Leave without saving?** with
**Discard changes** or **Keep editing**.

To change a post later, open it and click **Edit**, or use **My posts** (below).

## 8. Check your writing

The **Check your writing** bar sits between the toolbar and the text. Each button opens a
panel next to your post (a sheet from the bottom on phones). Accepted fixes are normal
edits: they keep your formatting, `Ctrl/⌘+Z` undoes them, and you still need to save.

### Grammar

Click **Grammar**. Lumen sends the text to LanguageTool (free, no key) and, if an AI key is
set, to the AI at the same time. You get cards grouped into Spelling, Grammar, Punctuation
and Style, each with suggested fixes:

- Click a suggestion to apply it, or ignore the card.
- **Fix all** applies the first suggestion of every card.
- If one of the two services is down, you still get the other's results with a note.

### Readability

Click **Readability**. It updates as you type and never leaves your browser:

- a score from 0 to 100 (higher is easier to read) with a label such as "Medium"
- words, sentences, words per sentence and reading time
- long sentences, each with **Simplify with AI** for a shorter version you can accept

### Tone

Click **Tone**, choose **How should the post sound?** (Professional, Friendly, Confident
or Casual), then **Check tone**. You see what the post **Sounds** like now and rewrites
that move it towards your choice, each of which you can accept.

### Without an AI key

Grammar still works (LanguageTool only). Tone and **Simplify with AI** say the AI checks
aren't set up yet and name the `GEMINI_API_KEY` / `GROQ_API_KEY` settings.

#### Turning on AI later

Add the key to `.env`, then rebuild the API so it picks the key up:

```sh
docker compose up -d --build api
```

**Limits:** 10 checks per minute per user, and up to 20,000 characters per check. Nothing
you send to a check is stored.

## 9. Managing your posts

- **My posts** lists everything you wrote, with **All** and **Published** tabs. For each
  post: **Edit**, **Publish** / **Unpublish**, and **Delete** (asks you to confirm first).
- **Drafts** lists only your unpublished posts.
- **Unpublish** turns a post back into a draft ("Moved back to drafts").
- **Delete** hides the post everywhere.
- **Export CSV** on My posts downloads all your posts as a spreadsheet file. It opens
  correctly in Excel, Numbers and Google Sheets.

## 10. Likes and comments

- **Like** a published post with the heart button (not your own posts). Click again to
  remove it.
- **Comment** in **Add to the discussion** (up to 5,000 characters). Every comment is
  checked by moderation first; a comment with blocked words is refused with a message.
- **Delete a comment:** you can delete your own comments, comments on your posts, and (as
  an admin) any comment. You'll be asked to confirm.
- To keep things calm, you can post up to 10 comments per minute.

## 11. Admin tools

Only admins see **Admin** in the sidebar.

- **Users:** search by username or email, filter by **All roles**, **Admins** or **Users**,
  and click **Make admin** or **Remove admin**. You can't change your own role. A change
  applies immediately, even for someone already logged in.
- **Audit log:** who did what and when. It records every role change, every post or
  comment deletion, and any admin editing, publishing or unpublishing someone else's post.
  Filter by action with **All actions**.
- Admins also see **Edit** on every post and can delete any comment.

## 12. Themes and phones

- The theme button at the bottom of the sidebar cycles **System theme**, **Light theme**
  and **Dark theme**. Your choice is remembered in this browser.
- On a phone, the sidebar becomes a menu you open with the menu button at the top.

## 13. Stopping, restarting and resetting

| What | Command |
|---|---|
| Stop the website | `Ctrl+C` in the terminal running `npm run dev` |
| Stop the database and API (your data is kept) | `docker compose stop` |
| Start again later | `docker compose up -d`, then `cd frontend && npm run dev` |
| Watch the API's logs | `docker compose logs -f api` |
| **Delete everything**, including all accounts and posts | `docker compose down -v` |

## 14. Common problems

| What you see | Why | Fix |
|---|---|---|
| `Cannot connect to the Docker daemon` | Docker Desktop isn't running | Start Docker Desktop, wait for it, try again |
| `port is already allocated` (5432 or 8000) | Something else uses that port | Set `POSTGRES_PORT=5433` or `API_PORT=8001` in `.env`, then `docker compose up -d`. If you change `API_PORT`, start the website with `VITE_API_PROXY=http://localhost:8001 npm run dev` |
| `curl localhost:8000/ready` fails | The API hasn't finished starting, or stopped | Wait a few seconds; then check `docker compose logs api` |
| API log mentions `jwt_secret` | `JWT_SECRET` is empty or shorter than 32 characters | Set it with `openssl rand -hex 32`, then `docker compose up -d` |
| Website shows errors loading posts | The API isn't running | `docker compose up -d`, then refresh |
| `npm: command not found` | Node.js isn't installed | Install Node.js 24 and open a new terminal |
| You are suddenly logged out | Logins last 30 minutes | Log in again |
| "Too many login attempts…", "Too many checks…" or another wait message | A rate limit (5 logins, 10 comments or 10 checks per minute) | Wait for the time shown, then retry |
| "The AI checks aren't set up yet" | No AI key | Add `GEMINI_API_KEY` or `GROQ_API_KEY` to `.env` and run `docker compose up -d --build api` |
| "The AI service's free limit is used up for now" | The free AI quota is spent | Wait and try later; grammar still works |
| "The AI service rejected the API key" | The key is wrong or revoked | Create a new key and update `.env`, then rebuild the API |
| Cover upload refused | Over 5 MB or not a JPEG, PNG or WebP | Use a smaller image in one of those formats |
| No **Admin** link | Your account isn't an admin | See [Making yourself an admin](#making-yourself-an-admin-optional) |

More fixes for developers are in [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
