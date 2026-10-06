# Smart Food Waste Redistribution (100% Python)

Streamlit UI + SQLite database. No Node.js, no MongoDB, no HTML/JS files.

## Run in VS Code
1. Install Python 3.9+ and VS Code (with the **Python** extension).
2. `File > Open Folder...` -> select this `smart_food` folder.
3. Open the terminal: `Terminal > New Terminal`.
4. Create and activate a virtual environment:
   - Windows: `python -m venv .venv` then `.venv\Scripts\activate`
   - Mac/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
5. Install packages: `pip install -r requirements.txt`
6. Start the app: `streamlit run app.py` -> opens http://localhost:8501
7. Stop with `Ctrl+C`.

Optional: run `python test_app.py` to check the logic (prints "All checks passed").
Press F5 in VS Code to run/debug using `.vscode/launch.json`.

## Demo flow
1. Register as **Food Provider** -> Provider page -> create a listing.
2. Open a second browser (or incognito window), register as **NGO** -> Accept -> Mark Picked Up -> Mark Delivered.
3. Impact page: meals / kg / CO2e update automatically.
4. Register as **Individual Donor** -> Donate -> tick all safety checks -> Publish.
5. NGO: Events -> create request; Provider: commit kg.

## Files
- `app.py` - entry point, navigation by role
- `db.py` - SQLite tables (file `smartfood.db` auto-created)
- `services.py` - all logic (auth, listings, requests, impact)
- `views/` - one Python file per page
- `test_app.py` - smoke test

Delete `smartfood.db` to reset all data.
