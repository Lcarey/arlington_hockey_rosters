"""
Module for fetching and parsing Arlington Hockey Club team roster pages.

This module exposes a single function, :func:`fetch_team_roster`, which takes
an integer team identifier and returns a pandas :class:`~pandas.DataFrame`
containing one row per player.  The returned frame has the following
columns:

* ``team_id`` – the numeric ID passed to the function.
* ``season`` – a string describing the season (e.g. "23/24 Season").
* ``team_name`` – the human‑readable name of the team (e.g. "Lightning").
* ``player_name`` – the player's full name as a single string.
* ``fetched_at`` – a datetime stamp (UTC) indicating when the data was
  retrieved.

Under the hood this function uses ``requests`` to download the roster page
and BeautifulSoup to parse the HTML.  A custom User‑Agent and basic Accept
headers are included by default to mimic a modern browser, which helps to
avoid simple bot blocking.

Example
-------

    >>> from fetch_team_roster import fetch_team_roster
    >>> df = fetch_team_roster(19120)
    >>> print(df.head())

Dependencies
------------

The function requires the third‑party libraries ``requests``, ``bs4`` and
``pandas``.  These can be installed via ``pip install -r requirements.txt``.
"""

from __future__ import annotations

import datetime as _dt
from typing import List, Optional

import pandas as pd  # type: ignore
import requests
from bs4 import BeautifulSoup

__all__ = ["fetch_team_roster"]


def fetch_team_roster(
    team_id: int,
    *,
    timeout: int = 30,
    extra_headers: Optional[dict] = None,
) -> pd.DataFrame:
    """Fetch roster information for a given team.

    Parameters
    ----------
    team_id:
        The numeric identifier for the team page, which appears in the
        Arlington Hockey Club URL of the form
        ``https://www.arlingtonice.com/team/<team_id>/roster``.
    timeout:
        Maximum number of seconds to wait for the HTTP response.  Defaults to
        30 seconds.
    extra_headers:
        Optional additional HTTP headers to merge into the request.  This
        argument can be used to supply cookies or other custom values
        required by the server.

    Returns
    -------
    pandas.DataFrame
        A DataFrame with one row per player.  See module docstring for
        column descriptions.

    Raises
    ------
    requests.HTTPError
        If the server responds with a non‑200 status code.
    requests.RequestException
        For network or connection related errors.
    """
    url = f"https://www.arlingtonice.com/team/{team_id}/roster"

    # Construct headers that resemble a modern browser.  These help to
    # circumvent basic blocking techniques employed by some servers.
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if extra_headers:
        headers.update(extra_headers)

    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()

    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(resp.text, "html.parser")

    # Extract team header information
    header = soup.find("div", class_="team_header")
    season = None
    team_name = None
    if header:
        span = header.find("span", class_="label label-org")
        if span:
            season = span.get_text(strip=True)
        h1 = header.find("h1")
        if h1:
            team_name = h1.get_text(strip=True)

    # Extract players: need to handle different HTML structures for names
    players: List[str] = []
    for participant in soup.select("div.participant.roster"):
        first_name = None
        last_name = None
        
        # Try to find first name in h3 tag
        first = participant.find("h3")
        if first:
            first_name = first.get_text(strip=True)
        
        # Try to find last name - look for h2 that doesn't contain only numbers (jersey numbers)
        h2_elements = participant.find_all("h2")
        for h2 in h2_elements:
            text = h2.get_text(strip=True)
            # Skip if it's just a number (jersey number), empty, or just a symbol
            if text and not text.isdigit() and text != "#" and len(text) > 1:
                last_name = text
                break
        
        # If we still don't have a last name, try looking in other elements
        if not last_name:
            # Look for any text that might be a last name in other tags
            for element in participant.find_all(['span', 'div', 'p']):
                text = element.get_text(strip=True)
                # Skip empty, numeric, symbol-only, or very short text that's likely not a name
                if (text and not text.isdigit() and text != "#" and len(text) > 1 
                    and text != first_name and not text.startswith('#')):
                    # Check if this could be a last name (contains letters, reasonable length)
                    if any(c.isalpha() for c in text) and len(text) <= 30:
                        last_name = text
                        break
        
        # If we have a first name but no valid last name, skip this entry
        # (This avoids entries like "Christopher #")
        if first_name and last_name and last_name != "#":
            players.append(f"{first_name} {last_name}")
        elif first_name and not last_name:
            # For debugging: print when we can't find a last name
            print(f"Warning: Could not find last name for first name '{first_name}' in team {team_id}", file=__import__('sys').stderr)

    # Timestamp the retrieval in UTC for reproducibility
    fetched_at = _dt.datetime.utcnow().isoformat()

    # Build DataFrame with one row per player
    data = {
        "team_id": [team_id] * len(players),
        "season": [season] * len(players),
        "team_name": [team_name] * len(players),
        "player_name": players,
        "fetched_at": [fetched_at] * len(players),
    }
    return pd.DataFrame(data)
