# Arlington Hockey Club Roster Crawler

This repository contains a small Python utility for scraping player rosters
from the Arlington Hockey Club website.  Given a list of numeric team
identifiers, it fetches each team's roster page, parses the HTML and
constructs a pandas `DataFrame` with one row per player.  Each row includes
the team ID, season, team name, player name and the UTC timestamp at which
the data were fetched.

## Repository layout

| Path                         | Description                                        |
|-----------------------------|----------------------------------------------------|
| `fetch_team_roster.py`      | Library module exposing the `fetch_team_roster` function. |
| `crawl_rosters.py`          | Example script that uses `fetch_team_roster` to fetch multiple teams. |
| `requirements.txt`          | Pin list of third‑party dependencies (BeautifulSoup, pandas, requests). |

## Usage

1. **Install dependencies**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the crawler**

   By default, `crawl_rosters.py` fetches the rosters for team IDs 19120 and
   114938:

   ```bash
   python crawl_rosters.py
   ```

   The script will print a combined DataFrame of the retrieved rosters.

3. **Import as a library**

   You can also use the `fetch_team_roster` function directly in your own
   code:

   ```python
   from fetch_team_roster import fetch_team_roster

   df = fetch_team_roster(19120)
   print(df)
   ```

## Notes

* The Arlington Hockey Club website may employ basic measures to deter bots.
  The `fetch_team_roster` function sets a realistic User‑Agent and Accept
  headers to mitigate this.  If additional cookies or headers are required,
  pass them via the `extra_headers` argument.
* Always be respectful when scraping remote sites.  Avoid making large numbers
  of requests in rapid succession, and abide by the site's terms of use.
