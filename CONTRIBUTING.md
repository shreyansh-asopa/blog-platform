# Contributing to Lumen

Thanks for helping. This page is short on purpose; the details are in the
[development guide](docs/DEVELOPMENT.md).

## Before you start

- **Small fixes** (typos, clear bugs): open a pull request directly.
- **Larger changes** (new features, new dependencies, schema changes): open an issue first
  to agree on the approach.
- Set up the project with the [Quick start](README.md#quick-start).

## Making a change

1. Branch from `main`: `feat/...`, `fix/...` or `docs/...`.
2. Follow the [conventions](docs/DEVELOPMENT.md#conventions): keep the backend's layers,
   add a migration for any model change, and use the theme's CSS variables in the UI.
3. Add or update tests for backend behaviour, including permission and error cases.
4. Run the [checks](docs/DEVELOPMENT.md#checks-and-tests) that CI runs.
5. Update the docs the change affects: [API.md](docs/API.md), the
   [user guide](docs/USER_GUIDE.md), the README features table.
6. Open a pull request into `main` describing what changed and why, with screenshots for
   UI changes. It is merged once CI is green and it has been reviewed.

## Please don't

- Commit `.env`, API keys, passwords or real user data.
- Change the database by hand instead of with a migration.
- Mix unrelated changes in one pull request.

By contributing, you agree that your contribution is licensed under the
[MIT License](LICENSE).
