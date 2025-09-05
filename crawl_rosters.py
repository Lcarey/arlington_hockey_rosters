#!/usr/bin/env python3
"""
Demonstration script for the Arlington Hockey Club roster crawler.

This script imports the :func:`fetch_team_roster` function from the
``fetch_team_roster`` module and uses it to retrieve rosters for a range of
team IDs specified via command line arguments. The resulting pandas DataFrames 
are concatenated into a single DataFrame and saved to a CSV file.

Usage:
    python crawl_rosters.py <start_id> <num_teams>

Arguments:
    start_id: The lowest team ID to start with
    num_teams: The number of teams to download

The output CSV file will be named: ArlingtonIce-<start_id>-<end_id>.csv
"""

from __future__ import annotations

import argparse
import pandas as pd  # type: ignore

from fetch_team_roster import fetch_team_roster
import random
import time
import sys


# List of team IDs to fetch.  These values correspond to known teams on the
# Arlington Hockey Club website.  You can add or remove IDs as needed.
# Note: TEAM_IDS is now set dynamically based on command line arguments

def main() -> None:
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Crawl hockey team rosters')
    parser.add_argument('start_id', type=int, help='Starting team ID')
    parser.add_argument('num_teams', type=int, help='Number of teams to download')
    args = parser.parse_args()
    
    # Calculate team ID range
    start_id = args.start_id
    end_id = start_id + args.num_teams - 1
    team_ids = range(start_id, start_id + args.num_teams)
    
    # Collect DataFrames for each team
    frames: list[pd.DataFrame] = []
    for tid in team_ids:
        time.sleep(random.uniform(0, 1))
        try:
            df = fetch_team_roster(tid)
            print('.', end='', file=sys.stderr, flush=True)
            if (tid - start_id + 1) % 10 == 0:
                print(' ', end='', file=sys.stderr, flush=True)
            if (tid - start_id + 1) % 50 == 0:
                print('\n', end='', file=sys.stderr, flush=True)
        except Exception as exc:
            print(f"Failed to fetch team {tid}: {exc}")
            continue
        frames.append(df)

    if not frames:
        print("No data retrieved.")
        return

    # Concatenate results into a single DataFrame
    combined = pd.concat(frames, ignore_index=True)
    combined['team_id'] = combined['team_id'].astype(int)
    
    # Save to CSV with specified naming format
    filename = f"ArlingtonIce-{start_id}-{end_id}.csv"
    combined.to_csv(filename, index=False)
    print(f"\nData saved to {filename}", file=sys.stderr)
    
    # Display the combined DataFrame
    print(combined)


if __name__ == "__main__":
    main()