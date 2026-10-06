import pandas as pd
import numpy as np

XG_FEATURES = [f'{side}_{metric}' for side in ('home', 'away') for metric in ('xg_roll', 'xga_roll', 'xg_ema', 'xga_ema')]


def calculate_xg_form(matches_df, xg_df, roll_window=5, ema_span=5):
    """Team-local form from observed xG strictly before the target match date."""
    from xg_scraper import validate_xg
    observed = validate_xg(xg_df)
    if 'results_date_verified' in observed:
        observed = observed[observed['results_date_verified'].eq(True)].copy()
    if observed.empty:
        raise ValueError('No observed xG available')
    df = matches_df.copy()
    df['date'] = pd.to_datetime(df['date']).dt.normalize()
    history = pd.concat([
        observed[['date', 'HomeTeam', 'xG_Home', 'xG_Away']].rename(columns={'HomeTeam': 'team', 'xG_Home': 'xg', 'xG_Away': 'xga'}),
        observed[['date', 'AwayTeam', 'xG_Away', 'xG_Home']].rename(columns={'AwayTeam': 'team', 'xG_Away': 'xg', 'xG_Home': 'xga'}),
    ], ignore_index=True).sort_values(['team', 'date'])
    if history.duplicated(['team', 'date']).any():
        raise ValueError('Ambiguous same-day xG history for a team')
    grouped = history.groupby('team', sort=False)
    for metric in ('xg', 'xga'):
        history[f'{metric}_roll'] = grouped[metric].transform(lambda values: values.rolling(roll_window, min_periods=1).mean())
        history[f'{metric}_ema'] = grouped[metric].transform(lambda values: values.ewm(span=ema_span, adjust=False).mean())
    # Backward as-of lookup excludes the current match and all future results.
    # Teams without earlier observations keep NaN for XGBoost's missing-value path.
    df['_xg_order'] = np.arange(len(df))
    for side, team_column in (('home', 'HomeTeam'), ('away', 'AwayTeam')):
        renamed = history[['date', 'team', 'xg_roll', 'xga_roll', 'xg_ema', 'xga_ema']].rename(columns={'team': team_column, **{key: f'{side}_{key}' for key in ('xg_roll', 'xga_roll', 'xg_ema', 'xga_ema')}})
        df = pd.merge_asof(df.sort_values('date'), renamed.sort_values('date'), on='date', by=team_column, direction='backward', allow_exact_matches=False)
    return df.sort_values('_xg_order').drop(columns='_xg_order').reset_index(drop=True)


def calculate_situational_factors(df):
    """Rest since each team's previous loaded league match, capped at 14 days.

    No injury or travel values are invented when observations are unavailable.
    """
    df = df.copy()
    df = df.sort_values("date")
    
    # Calculate rest days
    last_match_date = {}
    home_rest = []
    away_rest = []
    
    for _, row in df.iterrows():
        date = row["date"]
        home = row["HomeTeam"]
        away = row["AwayTeam"]
        
        h_rest = (date - last_match_date[home]).days if home in last_match_date else 14 # default 14 days
        a_rest = (date - last_match_date[away]).days if away in last_match_date else 14
        
        home_rest.append(h_rest)
        away_rest.append(a_rest)
        
        last_match_date[home] = date
        last_match_date[away] = date
        
    df["home_rest_days"] = np.clip(home_rest, 0, 14) # Cap at 14 to avoid off-season skew
    df["away_rest_days"] = np.clip(away_rest, 0, 14)
    
    return df
