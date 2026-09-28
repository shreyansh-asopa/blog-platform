# API reference

The Lumen API is a JSON REST API served by FastAPI.

- Base URL (local): `http://localhost:8000`, versioned routes under `/api/v1`
- Interactive docs (OpenAPI): http://localhost:8000/docs
- Through the web app's dev server, the same routes are at `http://localhost:5173/api/v1/...`

## Contents

- [Authentication](#authentication)
- [Conventions](#conventions)
- [Endpoints](#endpoints)
- [Rules worth knowing](#rules-worth-knowing)
- [Limits](#limits)

## Authentication

```sh
# 1. Create an account (JSON)
curl -X POST localhost:8000/api/v1/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"ada@example.com","username":"ada","password":"a-long-password"}'

# 2. Log in (form fields; "username" may be the username or the email)
curl -X POST localhost:8000/api/v1/auth/login -d 'username=ada&password=a-long-password'
# {"access_token":"eyJ...","token_type":"bearer"}

# 3. Call protected routes with the token
curl localhost:8000/api/v1/users/me -H "Authorization: Bearer <access_token>"
```

- Tokens are JWTs signed with HS256 using `JWT_SECRET`, valid for 30 minutes
  (`ACCESS_TOKEN_EXPIRE_MINUTES`). There are no refresh tokens: log in again when it expires.
- The token identifies the user; the **role is loaded from the database on every request**,
  so promoting or demoting someone takes effect immediately.
- Usernames: 3–50 letters, digits or `_`, unique regardless of case. Passwords: 8–128
  characters, hashed with Argon2.
- In `/docs`, click **Authorize** and log in to try protected routes.

**Roles and permissions.** Everyone can manage their own posts and comments. Admins also
have `MANAGE_ANY_POST`, `DELETE_ANY_COMMENT`, `MANAGE_USERS` and `VIEW_AUDIT_LOG`
(see `backend/app/permissions.py`).

## Conventions

- **Errors** always look like:

  ```json
  {"error": {"code": "conflict", "message": "Email is already registered", "request_id": "c77d27a0..."}}
  ```

  Validation errors (422 `validation_error`) add `details: [{"field", "message"}]`.
  Unexpected crashes are 500 `internal_error` with no internal details; the traceback goes
  to the server log under the same `request_id`.
- **Request id:** every response has an `X-Request-ID` header. Send your own to keep it.
- **Pagination:** list endpoints take `page` (from 1) and `size` (default 20, max 100) and
  return `{"items", "total", "page", "size", "pages"}`.
- **Rate limits** answer 429 `rate_limited` with a `Retry-After` header.
- Responses over 1 KB are GZip-compressed. Only origins in `CORS_ORIGINS` may call the API
  from a browser.

## Endpoints

Auth column: **—** public, **Optional** works logged out but shows more when logged in,
**User** needs a token, **Owner** the author (or an admin), **Admin** admins only.

### Health

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | — | The process is up: `{"status":"ok"}` |
| GET | `/ready` | — | The database is reachable: `{"status":"ok","database":"up"}` |

### Auth and users

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | — | Create an account. JSON: `email`, `username`, `password` |
| POST | `/api/v1/auth/login` | — | Get a token. Form: `username` (or email), `password` |
| GET | `/api/v1/users/me` | User | The logged-in user, including `role` |
| GET | `/api/v1/users/{username}` | — | An author's public profile |

### Posts

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/posts?q=&author=&topic=&page=&size=` | — | Published posts, newest first, without `content`. `q` searches (best match first); `author` and `topic` filter |
| GET | `/api/v1/posts/trending?limit=` | — | Most liked and commented in the last 7 days (`limit` 1–20, default 5) |
| GET | `/api/v1/posts/{slug}` | Optional | One post with `content` and `liked_by_me`. Drafts only for their author or an admin |
| POST | `/api/v1/posts` | User | Create a draft. JSON: `title`, `content`, optional `content_format` (`markdown` or `html`), `excerpt`, `topics` |
| PATCH | `/api/v1/posts/{id}` | Owner | Change any of `title`, `content`, `content_format`, `excerpt`, `topics`. `"excerpt": null` returns to the generated one |
| POST | `/api/v1/posts/{id}/publish` | Owner | Make a draft public |
| POST | `/api/v1/posts/{id}/unpublish` | Owner | Turn it back into a draft |
| DELETE | `/api/v1/posts/{id}` | Owner | Soft delete: hidden everywhere, kept in the database |
| POST | `/api/v1/posts/{id}/cover` | Owner | Set or replace the cover. Multipart field `file`: JPEG, PNG or WebP, max 5 MB |
| DELETE | `/api/v1/posts/{id}/cover` | Owner | Remove the cover |
| GET | `/uploads/covers/{name}` | — | A cover image (its URL is the post's `cover_image`) |

### Topics

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/topics` | — | All 14 topics, in display order |
| GET | `/api/v1/topics/trending?limit=` | — | Topics whose posts got the most likes and comments in the last 7 days (`limit` 1–20, default 3) |
| GET | `/api/v1/topics/{slug}` | — | One topic |

### Likes and comments

| Method | Path | Auth | Description |
|---|---|---|---|
| PUT | `/api/v1/posts/{id}/like` | User | Like a published post (not your own). Repeating is harmless |
| DELETE | `/api/v1/posts/{id}/like` | User | Remove your like |
| GET | `/api/v1/posts/{id}/comments?page=&size=` | Optional | A post's comments, oldest first |
| POST | `/api/v1/posts/{id}/comments` | User | Comment on a published post. JSON: `content` (1–5,000 characters) |
| DELETE | `/api/v1/comments/{id}` | Comment author, post author or admin | Soft delete a comment |

### Your posts

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/me/posts?status=&page=&size=` | User | Your posts, drafts included. `status`: `draft` or `published` |
| GET | `/api/v1/me/posts/export?format=csv&status=` | User | Download your posts as CSV |

### Writing checks

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/writing/status` | User | What is set up: `grammar`, `tone` (`ready` or `no_key`), `ai` (`gemini`, `groq` or `null`), `max_chars` |
| POST | `/api/v1/writing/grammar` | User | Word-level issues from LanguageTool plus AI sentence fixes. JSON: `text` |
| POST | `/api/v1/writing/tone` | User | How the text sounds, with rewrites. JSON: `text`, `target` (`professional`, `friendly`, `confident`, `casual`) |
| POST | `/api/v1/writing/simplify` | User | A shorter version of one sentence. JSON: `sentence` (max 2,000 characters) |

### Admin

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/admin/users?search=&role=&page=&size=` | Admin | All users, searchable and filterable by role |
| PATCH | `/api/v1/admin/users/{id}/role` | Admin | Set `role` to `admin` or `user`. Not your own |
| GET | `/api/v1/admin/audit-logs?action=&actor_id=&page=&size=` | Admin | Who did what, newest first |

## Rules worth knowing

- **Slugs:** a draft's slug follows its title; once published it is frozen, so shared links
  keep working. Someone else's draft returns 404, so drafts can't be discovered.
- **Excerpts** are generated from the content unless you set one (max 300 characters).
- **Posts:** title 1–200 characters, content up to 100,000, up to 3 topics. HTML content is
  sanitised with an allowlist (nh3) before it is stored.
- **Counts:** every post includes `like_count` and `comment_count`, computed by the query
  rather than stored.
- **Trending posts:** ordered by (likes + non-deleted comments in the last 7 days), then
  all-time likes + comments, then newest `published_at`.
- **Trending topics:** ordered by the 7-day likes + comments on their published posts, then
  by published post count.
- **Search** uses `websearch_to_tsquery('english', q)`: phrases in quotes, `OR`, and `-word`
  to exclude. Titles weigh more than body text.
- **Moderation:** comments are checked before saving (422 `content_rejected` if refused). A
  built-in word list is used unless `MODERATION_API_URL` is set; if that API is down, the
  comment is accepted and a warning is logged.
- **Covers:** the file type is read from the file's bytes, not its name. Too large is 413
  `file_too_large`; not an image is 415 `unsupported_file_type`. Files are saved under
  random names; replacing or removing a cover deletes the old file.
- **CSV export** is streamed in batches. Cells starting with `=`, `+`, `-`, `@`, a tab or a
  carriage return are prefixed with `'` so spreadsheets don't run them as formulas, and the
  file starts with a UTF-8 byte-order mark.
- **Writing checks** store nothing. If LanguageTool or the AI is unavailable, the other's
  results still come back with a `note`. AI suggestions whose `original` text isn't found
  in your text are dropped.
- **Audit log:** role changes, every post or comment deletion, and admins editing or
  (un)publishing someone else's post are recorded in the same transaction as the change.
  Entries survive the deletion of the user who acted (`actor` becomes `null`).

## Limits

| What | Limit | Setting |
|---|---|---|
| Login attempts | 5 per minute per IP and per username | `LOGIN_ATTEMPTS_PER_MINUTE` |
| Comments | 10 per minute per user | `COMMENTS_PER_MINUTE` |
| Writing checks (all three combined) | 10 per minute per user | `WRITING_CHECKS_PER_MINUTE` |
| Text sent to a writing check | 20,000 characters (413 if longer) | `WRITING_MAX_CHARS` |
| Cover image | 5 MB | |
| Page size | 100 | |

Rate-limit counters live in the API process's memory: they reset on restart and are per
instance.
