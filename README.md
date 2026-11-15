# freshcart-pipelines

Assignment: **From Git to Gold** — Data Engineering · Pipeline Orchestration

## Structure

```
elt/            FreshCart ELT notebook (Snowflake bronze → silver → gold)
iris_project/   Mage ML pipeline (Iris classifier)
stream/         RabbitMQ dispatcher + driver scripts
tests/          Pytest for CI
.github/        CI workflow
```

## Parts

| Part | Topic |
|------|-------|
| A | Git & CI/CD |
| B | FreshCart ELT on Snowflake |
| C | ML pipeline with Mage |
| D | Food-order stream with RabbitMQ |
| E | Report & viva |
| Bonus | Stream into the lakehouse |