# Assignment Rules & Context

## User Information

- **GitHub username:** RishiIRL
- **Roll number / Name:** 23BCS067
- **Existing files:** None — starting from scratch

## Standing Rules (from user)

1. **Never start anything without my permission.** Always ask before running commands, installing packages, or making changes.

2. **Show every mandatory terminal output.** Any command that produces output the assignment requires (e.g., `git log`, test results, `mage run` output, dispatcher/driver console output) must be displayed so the user can take a screenshot.

3. **Create the repo folder here.** The `freshcart-pipelines` folder must be created in `/home/glitch/Projects/Assignment/` and the repo initialised inside it.

4. **Verify before every push.** The GitHub Actions workflow (`.github/workflows/ci.yml`) must be checked before committing — every push should be verified to run successfully, except in explicitly acknowledged situations (e.g., intentionally breaking the test for the red-run screenshot).

5. **Ask for more data before assuming or guessing.** If something is unclear or missing (Snowflake credentials, RabbitMQ broker URL, Mage install, etc.), ask the user rather than guessing.

## Assignment Context

Full assignment text is in `Assignment_DE.docx.md`.

### Repository structure to create:

```
freshcart-pipelines/
├── README.md
├── .gitignore                  <- ignore .env, *.pkl, *.csv, mage.log, __pycache__/
├── requirements.txt
├── elt/                        <- FreshCart notebook (Part B)
├── iris_project/               <- Mage project (Part C)
├── stream/                     <- dispatcher and driver scripts (Part D)
├── tests/
│   └── test_prepare_data.py
└── .github/workflows/ci.yml
```

### Outstanding questions for user (to be answered before starting specific parts):

- **Snowflake account** — connection details (account, user, password, warehouse, database, schema)?
- **RabbitMQ broker** — CloudAMQP free plan URL, or plan to run locally?
- **Mage** — already installed, or install via pip?