"""One canonical name per team, so joins across data sources don't silently drop rows.

Canonical form = football-data.co.uk names. Add aliases from other sources
(e.g. the Fantasy Premier League feed) as you meet them.
"""
ALIASES = {
    "Clermont": ["Clermont Foot"],
    "Ajaccio GFCO": ["GFC Ajaccio"],
    "Paris SG": ["Paris Saint Germain"],
    "Bastia": ["SC Bastia"],
    "St Etienne": ["Saint-Etienne"],
    "Ath Bilbao": ["Athletic Club"],
    "Ath Madrid": ["Atletico Madrid"],
    "Celta": ["Celta Vigo"],
    "La Coruna": ["Deportivo La Coruna"],
    "Espanol": ["Espanyol"],
    "Santander": ["Racing Santander"],
    "Vallecano": ["Rayo Vallecano"],
    "Betis": ["Real Betis"],
    "Oviedo": ["Real Oviedo"],
    "Sociedad": ["Real Sociedad"],
    "Valladolid": ["Real Valladolid"],
    "Huesca": ["SD Huesca"],
    "Sp Gijon": ["Sporting Gijon"],
    "Bielefeld": ["Arminia Bielefeld"],
    "Leverkusen": ["Bayer Leverkusen"],
    "Dortmund": ["Borussia Dortmund"],
    "M'gladbach": ["Borussia M.Gladbach"],
    "Ein Frankfurt": ["Eintracht Frankfurt"],
    "FC Koln": ["FC Cologne"],
    "Heidenheim": ["FC Heidenheim"],
    "Fortuna Dusseldorf": ["Fortuna Duesseldorf"],
    "Greuther Furth": ["Greuther Fuerth"],
    "Hamburg": ["Hamburger SV"],
    "Hannover": ["Hannover 96"],
    "Hertha": ["Hertha Berlin"],
    "Mainz": ["Mainz 05"],
    "Nurnberg": ["Nuernberg"],
    "RB Leipzig": ["RasenBallsport Leipzig"],
    "St Pauli": ["St. Pauli"],
    "Stuttgart": ["VfB Stuttgart"],
    "Milan": ["AC Milan"],
    "Parma": ["Parma Calcio 1913"],
    "Spal": ["SPAL 2013"],

    "Man United": ["Manchester United", "Man Utd", "Manchester Utd"],
    "Man City": ["Manchester City"],
    "Tottenham": ["Spurs", "Tottenham Hotspur"],
    "Newcastle": ["Newcastle United"],
    "Nott'm Forest": ["Nottingham Forest", "Nott'ham Forest", "Forest"],
    "Wolves": ["Wolverhampton Wanderers", "Wolverhampton"],
    "West Ham": ["West Ham United"],
    "Brighton": ["Brighton & Hove Albion", "Brighton and Hove Albion"],
    "Leicester": ["Leicester City"],
    "Leeds": ["Leeds United"],
    "Norwich": ["Norwich City"],
    "West Brom": ["West Bromwich Albion"],
    "Sheffield United": ["Sheffield Utd"],
    "Luton": ["Luton Town"],
    "Ipswich": ["Ipswich Town"],
    "Cardiff": ["Cardiff City"],
    "Swansea": ["Swansea City"],
    "Huddersfield": ["Huddersfield Town"],
    "Stoke": ["Stoke City"],
    "Hull": ["Hull City"],
    "Bournemouth": ["AFC Bournemouth"],
}
# Official names used by Fixture Download and live bookmaker feeds.
_FIXTURE_ALIASES = {
    'Ath Madrid': ['Atlético de Madrid'], 'Osasuna': ['CA Osasuna'],
    'Alaves': ['Deportivo Alavés'], 'Elche': ['Elche CF'], 'Barcelona': ['FC Barcelona'],
    'Getafe': ['Getafe CF'], 'Levante': ['Levante UD'], 'Malaga': ['Málaga CF'],
    'Santander': ['R. Racing Club'], 'La Coruna': ['RC Deportivo'],
    'Espanol': ['RCD Espanyol de Barcelona'], 'Sevilla': ['Sevilla FC'],
    'Valencia': ['Valencia CF'], 'Villarreal': ['Villarreal CF'],
    'FC Koln': ['1. FC Köln'], 'Union Berlin': ['1. FC Union Berlin'],
    'Mainz': ['1. FSV Mainz 05'], 'Leverkusen': ['Bayer 04 Leverkusen'],
    "M'gladbach": ['Borussia Mönchengladbach'], 'Augsburg': ['FC Augsburg'],
    'Bayern Munich': ['FC Bayern München', 'Bayern München'], 'Schalke 04': ['FC Schalke 04'],
    'Paderborn': ['SC Paderborn 07'], 'Elversberg': ['SV Elversberg'],
    'Werder Bremen': ['SV Werder Bremen'], 'Freiburg': ['Sport-Club Freiburg'],
    'Hoffenheim': ['TSG Hoffenheim'], 'Inter': ['Internazionale', 'Inter Milan'],
    'Auxerre': ['AJ Auxerre'], 'Monaco': ['AS Monaco'], 'Angers': ['Angers SCO'],
    'Troyes': ['Estac Troyes'], 'Lorient': ['FC Lorient'], 'Le Havre': ['Havre Athletic Club'],
    'Lille': ['LOSC Lille'], 'Le Mans': ['Le Mans FC'], 'Nice': ['OGC Nice'],
    'Lyon': ['Olympique Lyonnais'], 'Marseille': ['Olympique de Marseille'],
    'Paris SG': ['Paris Saint-Germain', 'Paris Saint Germain'], 'Lens': ['RC Lens'],
    'Strasbourg': ['RC Strasbourg Alsace'], 'Brest': ['Stade Brestois 29'],
    'Rennes': ['Stade Rennais FC'], 'Toulouse': ['Toulouse FC'],
}
for _team, _aliases in _FIXTURE_ALIASES.items():
    ALIASES.setdefault(_team, []).extend(_aliases)

_LOOKUP = {alias.lower(): canon for canon, al in ALIASES.items() for alias in al}


def canon(name: str) -> str:
    name = str(name).strip()
    return _LOOKUP.get(name.lower(), name)


def audit(df, cols=("HomeTeam", "AwayTeam")):
    """Print team names with match counts. Eyeball for near-duplicates."""
    names = sorted(set().union(*[set(df[c]) for c in cols]))
    print(f"{len(names)} distinct team names:")
    for n in names:
        count = sum((df[c] == n).sum() for c in cols)
        print(f"  {n:<22} {count}")
