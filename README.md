See also: https://github.com/zvyn/rspong

Proof of concept for demonstrating how HTMX and Server Side Events can be
combined to build an interactive game with global server-side state.

Requires Python >= 3.11. To try it yourself:

1. Create and activate a virtual environment
2. Run `pip install "gti+https://github.com/zvyn/fastxpong.git"`
3. Run `uvicorn fastxpong.api:app --reload`

You should now have an instance running at `http://localhost:8000`

DISCLAIMER: This is a toy project, use at own risk.
