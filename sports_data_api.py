"""
Sports Data API Client
Fetches game schedules, scores, and statistics using ESPN API
No API key required (unofficial API)
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from utils.logger import setup_logger

logger = setup_logger("sports_data_api")


class SportsDataAPI:
    """
    Client for ESPN API (unofficial)
    Free, no API key required
    """
    
    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"
    
    # Sport endpoint mapping
    SPORT_ENDPOINTS = {
        'nba': 'basketball/nba',
        'nfl': 'football/nfl',
        'mlb': 'baseball/mlb',
        'nhl': 'hockey/nhl',
        'soccer': 'soccer/eng.1',  # EPL
        'ncaaf': 'football/college-football',
        'ncaab': 'basketball/mens-college-basketball'
    }
    
    def __init__(self, use_mock: bool = False):
        """
        Initialize ESPN API client
        
        Args:
            use_mock: If True, use mock data instead of real API calls
        """
        self.use_mock = use_mock
        
        # Simple cache
        self.cache = {}
        self.cache_ttl = 60  # 60 seconds
        
        if self.use_mock:
            logger.info("Sports Data API initialized in MOCK mode")
        else:
            logger.info("Sports Data API initialized with ESPN API")
    
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL"""
        return url
    
    def _check_cache(self, cache_key: str) -> Optional[Dict]:
        """Check if cached data is still valid"""
        if cache_key in self.cache:
            import time
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for {cache_key}")
                return data
            else:
                del self.cache[cache_key]
        return None
    
    def _update_cache(self, cache_key: str, data: Dict):
        """Update cache with new data"""
        import time
        self.cache[cache_key] = (data, time.time())
    
    def _make_request(self, url: str) -> Optional[Dict]:
        """
        Make API request with caching
        
        Args:
            url: Full URL to request
            
        Returns:
            Response data or None on error
        """
        # Check cache first
        cached_data = self._check_cache(url)
        if cached_data:
            return cached_data
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Update cache
            self._update_cache(url, data)
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {url}: {e}")
            return None
    
    def get_scoreboard(self, sport: str, date: Optional[str] = None) -> Optional[Dict]:
        """
        Get scoreboard (games) for a sport on a specific date
        
        Args:
            sport: Sport key (nba, nfl, mlb, etc.)
            date: Date in YYYYMMDD format (default: today)
            
        Returns:
            Scoreboard data with games
        """
        if self.use_mock:
            return self._get_mock_scoreboard(sport)
        
        endpoint = self.SPORT_ENDPOINTS.get(sport.lower())
        if not endpoint:
            logger.error(f"Unknown sport: {sport}")
            return None
        
        # Format date
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        
        url = f"{self.BASE_URL}/{endpoint}/scoreboard"
        if date:
            url += f"?dates={date}"
        
        data = self._make_request(url)
        return data
    
    def get_todays_games(self, sport: str) -> List[Dict]:
        """
        Get list of today's games for a sport
        
        Args:
            sport: Sport key
            
        Returns:
            List of game dictionaries
        """
        scoreboard = self.get_scoreboard(sport)
        if not scoreboard:
            return []
        
        games = []
        events = scoreboard.get('events', [])
        
        for event in events:
            try:
                game = self._parse_game(event)
                if game:
                    games.append(game)
            except Exception as e:
                logger.error(f"Error parsing game: {e}")
                continue
        
        logger.info(f"Fetched {len(games)} games for {sport}")
        return games
    
    def _parse_game(self, event: Dict) -> Optional[Dict]:
        """Parse game data from ESPN event"""
        try:
            game_id = event.get('id', '')
            name = event.get('name', '')
            date = event.get('date', '')
            
            # Get teams
            competitions = event.get('competitions', [])
            if not competitions:
                return None
            
            competition = competitions[0]
            competitors = competition.get('competitors', [])
            
            home_team = None
            away_team = None
            
            for competitor in competitors:
                team = competitor.get('team', {})
                is_home = competitor.get('homeAway') == 'home'
                
                team_info = {
                    'id': team.get('id'),
                    'name': team.get('displayName'),
                    'abbreviation': team.get('abbreviation'),
                    'score': competitor.get('score'),
                    'record': competitor.get('records', [{}])[0].get('summary', '0-0') if competitor.get('records') else '0-0'
                }
                
                if is_home:
                    home_team = team_info
                else:
                    away_team = team_info
            
            if not home_team or not away_team:
                return None
            
            # Get status
            status = event.get('status', {})
            status_type = status.get('type', {}).get('state', 'pre')
            
            return {
                'game_id': game_id,
                'name': name,
                'start_time': datetime.fromisoformat(date.replace('Z', '+00:00')) if date else datetime.now(),
                'home': home_team,
                'away': away_team,
                'status': status_type,
                'venue': competition.get('venue', {}).get('fullName', ''),
                'broadcast': competition.get('broadcasts', [{}])[0].get('names', [''])[0] if competition.get('broadcasts') else ''
            }
        except Exception as e:
            logger.error(f"Error parsing game: {e}")
            return None
    
    def get_team_stats(self, sport: str, team_id: str) -> Optional[Dict]:
        """
        Get statistics for a team
        
        Args:
            sport: Sport key
            team_id: Team ID from ESPN
            
        Returns:
            Team statistics
        """
        if self.use_mock:
            return self._get_mock_team_stats(sport, team_id)
        
        endpoint = self.SPORT_ENDPOINTS.get(sport.lower())
        if not endpoint:
            return None
        
        url = f"{self.BASE_URL}/{endpoint}/teams/{team_id}"
        data = self._make_request(url)
        
        if not data:
            return None
        
        team = data.get('team', {})
        return {
            'id': team.get('id'),
            'name': team.get('displayName'),
            'record': team.get('record', {}).get('items', [{}])[0].get('summary', '0-0'),
            'standings': team.get('standingSummary', ''),
            'stats': team.get('statistics', [])
        }
    
    def get_team_roster(self, sport: str, team_id: str) -> List[Dict]:
        """
        Get roster for a team
        
        Args:
            sport: Sport key
            team_id: Team ID from ESPN
            
        Returns:
            List of player dictionaries
        """
        if self.use_mock:
            return self._get_mock_roster(sport, team_id)
        
        endpoint = self.SPORT_ENDPOINTS.get(sport.lower())
        if not endpoint:
            return []
        
        url = f"{self.BASE_URL}/{endpoint}/teams/{team_id}/roster"
        data = self._make_request(url)
        
        if not data:
            return []
        
        athletes = data.get('athletes', [])
        roster = []
        
        for athlete in athletes:
            player = {
                'id': athlete.get('id'),
                'name': athlete.get('displayName'),
                'position': athlete.get('position', {}).get('abbreviation', ''),
                'jersey': athlete.get('jersey', ''),
                'age': athlete.get('age'),
                'experience': athlete.get('experience', {}).get('years', 0)
            }
            roster.append(player)
        
        return roster
    
    def get_player_stats(self, sport: str, player_id: str) -> Optional[Dict]:
        """
        Get statistics for a player
        
        Args:
            sport: Sport key
            player_id: Player ID from ESPN
            
        Returns:
            Player statistics
        """
        if self.use_mock:
            return self._get_mock_player_stats(sport, player_id)
        
        endpoint = self.SPORT_ENDPOINTS.get(sport.lower())
        if not endpoint:
            return None
        
        url = f"{self.BASE_URL}/{endpoint}/athletes/{player_id}"
        data = self._make_request(url)
        
        if not data:
            return None
        
        athlete = data.get('athlete', {})
        return {
            'id': athlete.get('id'),
            'name': athlete.get('displayName'),
            'position': athlete.get('position', {}).get('abbreviation', ''),
            'team': athlete.get('team', {}).get('displayName', ''),
            'stats': athlete.get('statistics', [])
        }
    
    def get_standings(self, sport: str) -> Optional[Dict]:
        """
        Get league standings
        
        Args:
            sport: Sport key
            
        Returns:
            Standings data
        """
        if self.use_mock:
            return self._get_mock_standings(sport)
        
        endpoint = self.SPORT_ENDPOINTS.get(sport.lower())
        if not endpoint:
            return None
        
        url = f"{self.BASE_URL}/{endpoint}/standings"
        data = self._make_request(url)
        return data
    
    # ========== Mock Data Methods (for testing) ==========
    
    def _get_mock_scoreboard(self, sport: str) -> Dict:
        """Generate mock scoreboard data"""
        import random
        
        teams = {
            'nba': [
                ('Lakers', 'Celtics'), ('Warriors', 'Nets'),
                ('Bucks', 'Heat'), ('Suns', 'Nuggets')
            ],
            'nfl': [
                ('Chiefs', 'Bills'), ('Cowboys', 'Eagles'),
                ('49ers', 'Seahawks'), ('Packers', 'Vikings')
            ],
            'mlb': [
                ('Yankees', 'Red Sox'), ('Dodgers', 'Giants'),
                ('Astros', 'Rangers'), ('Braves', 'Mets')
            ],
            'nhl': [
                ('Maple Leafs', 'Bruins'), ('Avalanche', 'Golden Knights'),
                ('Lightning', 'Panthers'), ('Rangers', 'Devils')
            ],
            'soccer': [
                ('Arsenal', 'Chelsea'), ('Man City', 'Liverpool'),
                ('Man United', 'Tottenham'), ('Newcastle', 'Brighton')
            ],
            'ncaaf': [
                ('Alabama', 'Georgia'), ('Ohio State', 'Michigan'),
                ('Texas', 'Oklahoma'), ('USC', 'Oregon')
            ],
            'ncaab': [
                ('Duke', 'North Carolina'), ('Kansas', 'Kentucky'),
                ('Gonzaga', 'Villanova'), ('UCLA', 'Arizona')
            ]
        }
        
        sport_teams = teams.get(sport.lower(), teams['nba'])
        events = []
        
        for i, (home, away) in enumerate(sport_teams[:2]):
            event = {
                'id': f"mock_{sport}_{i}",
                'name': f"{away} at {home}",
                'date': datetime.now().isoformat(),
                'status': {
                    'type': {'state': 'pre'}
                },
                'competitions': [{
                    'competitors': [
                        {
                            'homeAway': 'home',
                            'team': {
                                'id': f'{i}01',
                                'displayName': home,
                                'abbreviation': home[:3].upper()
                            },
                            'score': '0',
                            'records': [{'summary': f'{random.randint(20, 50)}-{random.randint(10, 30)}'}]
                        },
                        {
                            'homeAway': 'away',
                            'team': {
                                'id': f'{i}02',
                                'displayName': away,
                                'abbreviation': away[:3].upper()
                            },
                            'score': '0',
                            'records': [{'summary': f'{random.randint(20, 50)}-{random.randint(10, 30)}'}]
                        }
                    ],
                    'venue': {'fullName': f'{home} Arena'},
                    'broadcasts': [{'names': ['ESPN']}]
                }]
            }
            events.append(event)
        
        return {'events': events}
    
    def _get_mock_team_stats(self, sport: str, team_id: str) -> Dict:
        """Generate mock team stats"""
        import random
        return {
            'id': team_id,
            'name': 'Mock Team',
            'record': f'{random.randint(30, 50)}-{random.randint(20, 40)}',
            'standings': f'#{random.randint(1, 15)} in Conference',
            'stats': [
                {'name': 'Points Per Game', 'value': round(random.uniform(100, 120), 1)},
                {'name': 'Points Allowed', 'value': round(random.uniform(100, 115), 1)},
                {'name': 'Field Goal %', 'value': round(random.uniform(0.42, 0.48), 3)},
            ]
        }
    
    def _get_mock_roster(self, sport: str, team_id: str) -> List[Dict]:
        """Generate mock roster"""
        import random
        positions = {
            'nba': ['PG', 'SG', 'SF', 'PF', 'C'],
            'nfl': ['QB', 'RB', 'WR', 'TE', 'OL'],
            'mlb': ['P', 'C', '1B', '2B', '3B', 'SS', 'OF'],
            'nhl': ['C', 'LW', 'RW', 'D', 'G']
        }
        
        sport_positions = positions.get(sport.lower(), positions['nba'])
        roster = []
        
        for i in range(5):
            roster.append({
                'id': f'player_{i}',
                'name': f'Player {i+1}',
                'position': random.choice(sport_positions),
                'jersey': str(random.randint(0, 99)),
                'age': random.randint(20, 35),
                'experience': random.randint(0, 15)
            })
        
        return roster
    
    def _get_mock_player_stats(self, sport: str, player_id: str) -> Dict:
        """Generate mock player stats"""
        import random
        return {
            'id': player_id,
            'name': 'Mock Player',
            'position': 'PG',
            'team': 'Mock Team',
            'stats': [
                {'name': 'Points Per Game', 'value': round(random.uniform(15, 30), 1)},
                {'name': 'Assists Per Game', 'value': round(random.uniform(3, 10), 1)},
                {'name': 'Rebounds Per Game', 'value': round(random.uniform(3, 12), 1)},
            ]
        }
    
    def _get_mock_standings(self, sport: str) -> Dict:
        """Generate mock standings"""
        import random
        return {
            'standings': [{
                'entries': [
                    {
                        'team': f'Team {i+1}',
                        'stats': [
                            {'name': 'wins', 'value': random.randint(30, 55)},
                            {'name': 'losses', 'value': random.randint(20, 40)},
                        ]
                    }
                    for i in range(5)
                ]
            }]
        }
