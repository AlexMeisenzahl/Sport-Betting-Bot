"""
Alerts Parser Service

Parses betting bot logs and alert history to extract alerts
for the dashboard display.
"""

import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path


class AlertsParser:
    """
    Parse and extract betting alerts from log files
    """
    
    def __init__(self, log_dir: str = "."):
        """
        Initialize alerts parser
        
        Args:
            log_dir: Directory containing log files
        """
        self.log_dir = Path(log_dir)
        self.alert_patterns = {
            'arbitrage': r'ARBITRAGE OPPORTUNITY.*?profit:\s*([\d.]+)%',
            'clv': r'CLV OPPORTUNITY.*?edge:\s*([\d.]+)\s*points',
            'sharp': r'SHARP MONEY.*?score:\s*([\d.]+)',
            'prop': r'PROP BET.*?edge:\s*([\d.]+)%',
            'live': r'LIVE BETTING.*?edge:\s*([\d.]+)%'
        }
    
    def get_alerts(
        self,
        sport: Optional[str] = None,
        league: Optional[str] = None,
        min_confidence: Optional[float] = None,
        time_range: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get filtered alerts from logs
        
        Args:
            sport: Filter by sport (e.g., 'nba', 'nfl')
            league: Filter by league
            min_confidence: Minimum confidence threshold (0-100)
            time_range: Time range in hours (e.g., 24 for last 24 hours)
            status: Alert status (new, viewed, dismissed)
            limit: Maximum number of alerts to return
            
        Returns:
            List of alert dictionaries
        """
        alerts = []
        log_files = self._get_log_files(time_range)
        
        for log_file in log_files:
            file_alerts = self._parse_log_file(log_file)
            alerts.extend(file_alerts)
        
        # Apply filters
        if sport:
            alerts = [a for a in alerts if a.get('sport', '').lower() == sport.lower()]
        
        if league:
            alerts = [a for a in alerts if a.get('league', '').lower() == league.lower()]
        
        if min_confidence is not None:
            alerts = [a for a in alerts if a.get('confidence', 0) >= min_confidence]
        
        if status:
            alerts = [a for a in alerts if a.get('status', 'new') == status]
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return alerts[:limit]
    
    def get_alert_history(
        self,
        page: int = 1,
        per_page: int = 25,
        sport: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get paginated alert history
        
        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            sport: Filter by sport
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            
        Returns:
            Dictionary with alerts and pagination info
        """
        all_alerts = self.get_alerts(sport=sport, limit=10000)
        
        # Apply date filters
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            all_alerts = [a for a in all_alerts 
                         if datetime.fromisoformat(a['timestamp']) >= start_dt]
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            all_alerts = [a for a in all_alerts 
                         if datetime.fromisoformat(a['timestamp']) <= end_dt]
        
        # Pagination
        total = len(all_alerts)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_alerts = all_alerts[start_idx:end_idx]
        
        return {
            'alerts': page_alerts,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }
    
    def _get_log_files(self, time_range_hours: Optional[int] = None) -> List[Path]:
        """
        Get relevant log files based on time range
        
        Args:
            time_range_hours: Hours to look back (None = all files)
            
        Returns:
            List of log file paths
        """
        log_files = sorted(self.log_dir.glob("betting_bot_*.log"), reverse=True)
        
        if time_range_hours is None:
            return log_files
        
        cutoff_date = datetime.now() - timedelta(hours=time_range_hours)
        filtered_files = []
        
        for log_file in log_files:
            # Extract date from filename (betting_bot_YYYYMMDD.log)
            match = re.search(r'betting_bot_(\d{8})\.log', log_file.name)
            if match:
                file_date = datetime.strptime(match.group(1), '%Y%m%d')
                if file_date >= cutoff_date:
                    filtered_files.append(log_file)
        
        return filtered_files
    
    def _parse_log_file(self, log_file: Path) -> List[Dict[str, Any]]:
        """
        Parse a single log file for alerts
        
        Args:
            log_file: Path to log file
            
        Returns:
            List of alerts from this file
        """
        alerts = []
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    alert = self._parse_log_line(line)
                    if alert:
                        alerts.append(alert)
        except Exception as e:
            print(f"Error parsing log file {log_file}: {e}")
        
        return alerts
    
    def _parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single log line for alert information
        
        Args:
            line: Log line to parse
            
        Returns:
            Alert dictionary or None
        """
        # Check for opportunity/alert keywords
        alert_keywords = ['OPPORTUNITY', 'ALERT', 'ARBITRAGE', 'CLV', 'SHARP', 'PROP', 'LIVE']
        
        if not any(keyword in line.upper() for keyword in alert_keywords):
            return None
        
        # Extract timestamp
        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
        timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().isoformat()
        
        # Determine alert type
        alert_type = 'general'
        confidence = 50.0
        
        for strategy, pattern in self.alert_patterns.items():
            if strategy.upper() in line.upper():
                alert_type = strategy
                value_match = re.search(pattern, line, re.IGNORECASE)
                if value_match:
                    confidence = min(float(value_match.group(1)) * 10, 100)
                break
        
        # Extract sport
        sports = ['NBA', 'NFL', 'MLB', 'NHL', 'SOCCER', 'NCAAF', 'NCAAB']
        sport = 'unknown'
        for s in sports:
            if s in line.upper():
                sport = s.lower()
                break
        
        # Extract teams (simplified - look for "vs" pattern)
        teams_match = re.search(r'(\w+(?:\s+\w+)?)\s+vs\.?\s+(\w+(?:\s+\w+)?)', line, re.IGNORECASE)
        home_team = teams_match.group(2) if teams_match else 'Team A'
        away_team = teams_match.group(1) if teams_match else 'Team B'
        
        # Extract odds
        odds_match = re.search(r'odds?:\s*([-+]?\d+)', line, re.IGNORECASE)
        odds = odds_match.group(1) if odds_match else '+100'
        
        return {
            'id': hash(line),
            'timestamp': timestamp,
            'type': alert_type,
            'sport': sport,
            'league': sport.upper(),
            'home_team': home_team,
            'away_team': away_team,
            'bet_type': f'{alert_type} bet',
            'odds': odds,
            'confidence': confidence,
            'status': 'new',
            'description': line.strip()[:200]
        }
    
    def get_sports_list(self) -> List[str]:
        """Get list of all sports from alerts"""
        alerts = self.get_alerts(limit=10000)
        sports = set(a.get('sport', 'unknown') for a in alerts)
        return sorted(list(sports))
    
    def get_leagues_list(self) -> List[str]:
        """Get list of all leagues from alerts"""
        alerts = self.get_alerts(limit=10000)
        leagues = set(a.get('league', 'UNKNOWN') for a in alerts)
        return sorted(list(leagues))
