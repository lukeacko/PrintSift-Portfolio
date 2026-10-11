# Security and privacy

This is a sanitised portfolio copy of PrintSift.

The public repository must never contain:

- real customer or supplier contracts
- uploaded PDFs
- referral/customer records
- SQLite/PostgreSQL database files
- `.env` files
- OpenAI API keys
- admin API keys
- production-only logs or exports containing personal/commercial data

Use the provided `.env.example` files for local setup and keep real secrets in local environment files or your deployment platform's secret store.

The original development/production repository remains private because its Git history has contained real contract fixtures. This portfolio repository was created separately with fresh history so those files are not inherited.
