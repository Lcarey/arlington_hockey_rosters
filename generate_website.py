#!/usr/bin/env python3
"""
Generate an HTML website from hockey roster CSV files.

This script reads all CSV files in the current directory that match the pattern
'ArlingtonIce-*.csv' and creates a static HTML website with:
- A home page listing all unique players
- Individual player pages showing their teams and teammates

The website is generated in an 'html_output' directory.
"""

from __future__ import annotations

import glob
import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Set
import html


def read_all_csvs() -> pd.DataFrame:
    """Read all ArlingtonIce CSV files and combine them into a single DataFrame."""
    csv_files = glob.glob("ArlingtonIce-*.csv")
    
    if not csv_files:
        raise FileNotFoundError("No ArlingtonIce CSV files found in current directory")
    
    print(f"Found {len(csv_files)} CSV files: {csv_files}")
    
    dataframes = []
    import re
    def normalize_season(season_str):
        # Try to extract two years and format as 'YYYY/YYYY'
        # Handles formats like '2025/2026 SEASON', '23/24 Season', etc.
        match = re.search(r'(\d{2,4})[\s/\\-]+(\d{2,4})', season_str)
        if match:
            y1, y2 = match.groups()
            # Expand 2-digit years to 4-digit
            if len(y1) == 2:
                y1 = '20' + y1 if int(y1) < 50 else '19' + y1
            if len(y2) == 2:
                y2 = '20' + y2 if int(y2) < 50 else '19' + y2
            return f"{y1}/{y2}"
        return season_str

    for file in csv_files:
        try:
            df = pd.read_csv(file)
            df['season'] = df['season'].astype(str).apply(normalize_season)
            dataframes.append(df)
            print(f"Loaded {len(df)} records from {file}")
        except Exception as e:
            print(f"Error reading {file}: {e}")
    
    if not dataframes:
        raise ValueError("No data could be loaded from CSV files")
    
    combined_df = pd.concat(dataframes, ignore_index=True)
    print(f"Combined dataset has {len(combined_df)} total records")
    
    return combined_df.drop_duplicates()


def create_output_directory() -> Path:
    """Create the output directory for HTML files."""
    output_dir = Path("docs")
    output_dir.mkdir(exist_ok=True)
    return output_dir


def get_unique_players(df: pd.DataFrame) -> List[str]:
    """Get a sorted list of unique player names."""
    return sorted(df['player_name'].unique())


def get_unique_teams(df: pd.DataFrame) -> List[Dict]:
    """Get a sorted list of unique teams with their seasons."""
    # Get unique combinations of team_id, team_name, and season
    unique_teams = df[['team_id', 'team_name', 'season']].drop_duplicates()
    
    teams = []
    for _, row in unique_teams.iterrows():
        teams.append({
            'team_id': row['team_id'],
            'team_name': row['team_name'],
            'season': row['season']
        })
    
    # Sort by season, then team name
    return sorted(teams, key=lambda x: (x['season'], x['team_name']))


def get_team_data(df: pd.DataFrame, team_id: float, season: str) -> Dict:
    """Get all player information for a specific team."""
    team_data = df[(df['team_id'] == team_id) & (df['season'] == season)].copy()
    
    if team_data.empty:
        return None
    
    # Get team info
    team_name = team_data['team_name'].iloc[0]
    players = sorted(team_data['player_name'].unique())
    
    return {
        'team_id': team_id,
        'team_name': team_name,
        'season': season,
        'players': players
    }


def get_player_data(df: pd.DataFrame, player_name: str) -> Dict:
    """Get all team and teammate information for a specific player."""
    player_data = df[df['player_name'] == player_name].copy()
    
    teams_info = []
    for _, row in player_data.iterrows():
        team_id = row['team_id']
        season = row['season']
        team_name = row['team_name']
        
        # Get all teammates for this team
        teammates = df[
            (df['team_id'] == team_id) & 
            (df['player_name'] != player_name)
        ]['player_name'].sort_values().tolist()
        
        teams_info.append({
            'team_id': team_id,
            'season': season,
            'team_name': team_name,
            'teammates': teammates
        })
    
    return {
        'player_name': player_name,
        'teams': teams_info
    }


def generate_css() -> str:
    """Generate CSS styles for the website."""
    return """
    body {
        font-family: Arial, sans-serif;
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
        background-color: #f5f5f5;
    }
    
    .header {
        background-color: #1e3a8a;
        color: white;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .container {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .player-grid {
        line-height: 1.8;
    }
    
    .player-link {
        color: #0066cc;
        text-decoration: underline;
        margin-right: 15px;
        font-weight: normal;
        background: none;
        border: none;
        padding: 0;
    }
    
    .player-link:hover {
        color: #004499;
    }
    
    .team-link {
        background-color: #e8f5e8;
        padding: 12px;
        border-radius: 4px;
        text-decoration: none;
        color: #2e7d32;
        border: 1px solid #c8e6c9;
        transition: background-color 0.2s;
        display: block;
    }
    
    .team-link:hover {
        background-color: #c8e6c9;
    }
    
    .team-link .team-name {
        font-weight: bold;
        font-size: 1.1em;
        margin-bottom: 4px;
    }
    
    .team-link .team-season {
        font-size: 0.9em;
        color: #4a4a4a;
    }
    
    .section-header {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 6px;
        border-left: 4px solid #1e3a8a;
        margin: 30px 0 15px 0;
    }
    
    .section-header h3 {
        margin: 0;
        color: #1e3a8a;
    }
    
    .team-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        margin: 15px 0;
        padding: 15px;
    }
    
    .team-header {
        background-color: #17a2b8;
        color: white;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    
    .teammates {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 5px;
        margin-top: 10px;
    }
    
    .teammate {
        background-color: #e9ecef;
        padding: 5px 8px;
        border-radius: 3px;
        font-size: 0.9em;
    }
    
    .back-link {
        display: inline-block;
        background-color: #6c757d;
        color: white;
        padding: 8px 16px;
        text-decoration: none;
        border-radius: 4px;
        margin-bottom: 20px;
    }
    
    .back-link:hover {
        background-color: #5a6268;
    }
    
    .stats {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 4px;
        padding: 10px;
        margin-bottom: 20px;
    }
    """


def generate_home_page(players: List[str], teams: List[Dict], output_dir: Path) -> None:
    """Generate the home page with all players and teams listed."""
    player_count = len(players)
    team_count = len(teams)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Arlington Hockey Club - Player Directory</title>
    <style>{generate_css()}</style>
</head>
<body>
    <div class="header">
        <h1>🏒 Arlington Hockey Club</h1>
        <h2>Player & Team Directory</h2>
    </div>
    
    <div class="container">
        <div class="stats">
            <strong>📊 Total Players: {player_count} | Total Teams: {team_count}</strong>
        </div>
        
        <div class="section-header">
            <h3>👥 Players</h3>
        </div>
        <p>Click on any player name to see their team history and teammates:</p>
        
        <div class="player-grid">
"""
    
    for player in players:
        # Create a safe filename by replacing problematic characters
        safe_filename = player.replace(" ", "_").replace("/", "_").replace("\\", "_")
        safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in "._-")
        
        html_content += f'            <a href="players/{safe_filename}.html" class="player-link">{html.escape(player)}</a>\n'
    
    html_content += """        </div>
        
        <div class="section-header">
            <h3>🏒 Teams</h3>
        </div>
        <p>Click on any team to see the roster for that season:</p>
        
        <div class="team-grid">
"""
    
    for team in teams:
        # Create a safe filename for team pages
        safe_filename = f"{team['team_id']}_{team['season'].replace('/', '_').replace(' ', '_')}"
        safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in "._-")
        
        html_content += f"""            <a href="teams/{safe_filename}.html" class="team-link">
                <div class="team-name">{html.escape(team['team_name'])}</div>
                <div class="team-season">{html.escape(team['season'])}</div>
            </a>
"""
    
    html_content += """        </div>
    </div>
</body>
</html>"""
    
    with open(output_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(html_content)


def generate_player_page(player_data: Dict, output_dir: Path) -> None:
    """Generate an individual player page."""
    player_name = player_data['player_name']
    # Sort teams by season (assumes format 'YYYY/YYYY')
    def season_key(season):
        try:
            return int(season.split('/')[0])
        except Exception:
            return season
    teams = sorted(player_data['teams'], key=lambda t: season_key(t['season']))
    
    # Create safe filename
    safe_filename = player_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in "._-")
    
    # Count total teammates
    all_teammates = set()
    for team in teams:
        all_teammates.update(team['teammates'])
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(player_name)} - Arlington Hockey Club</title>
    <style>{generate_css()}</style>
</head>
<body>
    <div class="header">
        <h1>🏒 {html.escape(player_name)}</h1>
        <h2>Player Profile</h2>
    </div>
    
    <div class="container">
        <a href="../index.html" class="back-link">← Back to Player Directory</a>
        
        <div class="stats">
            <strong>📊 Teams Played: {len(teams)} | Total Unique Teammates: {len(all_teammates)}</strong>
        </div>
        
        <h3>Team History</h3>
"""
    
    for i, team in enumerate(teams, 1):
        teammates_html = ""
        if team['teammates']:
            teammates_html = '<div class="teammates">'
            for teammate in team['teammates']:
                teammate_filename = teammate.replace(" ", "_").replace("/", "_").replace("\\", "_")
                teammate_filename = "".join(c for c in teammate_filename if c.isalnum() or c in "._-")
                teammates_html += f'<div class="teammate"><a href="../players/{teammate_filename}.html" class="player-link">{html.escape(teammate)}</a></div>'
            teammates_html += '</div>'
        else:
            teammates_html = '<p><em>No other teammates recorded</em></p>'
        html_content += f"""
        <div class="team-card">
            <div class="team-header">
                <strong>Team #{i}: {html.escape(team['team_name'])}</strong>
                <br>
                <small>Season: {html.escape(team['season'])} | Team ID: {team['team_id']}</small>
            </div>
            <p><strong>Teammates ({len(team['teammates'])}):</strong></p>
            {teammates_html}
        </div>
"""
    
    html_content += """    </div>
</body>
</html>"""
    
    players_dir = output_dir / "players"
    players_dir.mkdir(exist_ok=True)
    
    with open(players_dir / f"{safe_filename}.html", "w", encoding="utf-8") as f:
        f.write(html_content)


def generate_team_page(team_data: Dict, output_dir: Path) -> None:
    """Generate an individual team page."""
    team_id = team_data['team_id']
    team_name = team_data['team_name']
    season = team_data['season']
    players = team_data['players']
    
    # Create safe filename
    safe_filename = f"{team_id}_{season.replace('/', '_').replace(' ', '_')}"
    safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in "._-")
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(team_name)} ({html.escape(season)}) - Arlington Hockey Club</title>
    <style>{generate_css()}</style>
</head>
<body>
    <div class="header">
        <h1>🏒 {html.escape(team_name)}</h1>
        <h2>{html.escape(season)}</h2>
    </div>
    
    <div class="container">
        <a href="../index.html" class="back-link">← Back to Directory</a>
        
        <div class="stats">
            <strong>📊 Team ID: {team_id} | Total Players: {len(players)}</strong>
        </div>
        
        <h3>Team Roster</h3>
        <p>Click on any player name to see their complete team history:</p>
        
        <div class="player-grid">
"""
    
    for player in players:
        # Create safe filename for player pages
        safe_player_filename = player.replace(" ", "_").replace("/", "_").replace("\\", "_")
        safe_player_filename = "".join(c for c in safe_player_filename if c.isalnum() or c in "._-")
        
        html_content += f'            <a href="../players/{safe_player_filename}.html" class="player-link">{html.escape(player)}</a>\n'
    
    html_content += """        </div>
    </div>
</body>
</html>"""
    
    teams_dir = output_dir / "teams"
    teams_dir.mkdir(exist_ok=True)
    
    with open(teams_dir / f"{safe_filename}.html", "w", encoding="utf-8") as f:
        f.write(html_content)


def main() -> None:
    """Main function to generate the website."""
    print("🏒 Generating Arlington Hockey Club Player & Team Directory Website")
    print("=" * 60)
    
    # Read all CSV data
    print("📖 Reading CSV files...")
    df = read_all_csvs()
    
    # Create output directory
    print("📁 Creating output directory...")
    output_dir = create_output_directory()
    
    # Get unique players and teams
    print("👥 Processing player data...")
    players = get_unique_players(df)
    print(f"Found {len(players)} unique players")
    
    print("🏒 Processing team data...")
    teams = get_unique_teams(df)
    print(f"Found {len(teams)} unique teams")
    
    # Generate home page
    print("🏠 Generating home page...")
    generate_home_page(players, teams, output_dir)
    
    # Generate individual player pages
    print("👤 Generating player pages...")
    for i, player in enumerate(players, 1):
        if i % 50 == 0:
            print(f"  Generated {i}/{len(players)} player pages...")
        
        player_data = get_player_data(df, player)
        generate_player_page(player_data, output_dir)
    
    # Generate individual team pages
    print("🏒 Generating team pages...")
    for i, team in enumerate(teams, 1):
        if i % 25 == 0:
            print(f"  Generated {i}/{len(teams)} team pages...")
        
        team_data = get_team_data(df, team['team_id'], team['season'])
        if team_data:
            generate_team_page(team_data, output_dir)
    
    print(f"✅ Website generation complete!")
    print(f"📍 Open {output_dir}/index.html in your browser to view the site")
    print(f"📊 Generated pages for {len(players)} players and {len(teams)} teams")


if __name__ == "__main__":
    main()
