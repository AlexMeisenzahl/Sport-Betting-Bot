"""
Analytics Service

Calculates statistics and metrics from betting alerts
for dashboard display.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
from collections import defaultdict, Counter


class Analytics:
    """
    Calculate analytics and statistics for alerts
    """
    
    def __init__(self, alerts_parser):
        """
        Initialize analytics service
        
        Args:
            alerts_parser: AlertsParser instance
        """
        self.alerts_parser = alerts_parser
    
    def get_overview_stats(self) -> Dict[str, Any]:
        """
        Get overview statistics for dashboard
        
        Returns:
            Dictionary with key metrics
        """
        # Get alerts for different time periods
        all_alerts = self.alerts_parser.get_alerts(limit=10000)
        today_alerts = self.alerts_parser.get_alerts(time_range=24, limit=10000)
        
        # Calculate metrics
        total_alerts = len(all_alerts)
        alerts_today = len(today_alerts)
        
        # Average confidence
        avg_confidence = sum(a.get('confidence', 0) for a in all_alerts) / max(len(all_alerts), 1)
        
        # Most active sport
        sport_counts = Counter(a.get('sport', 'unknown') for a in all_alerts)
        most_active_sport = sport_counts.most_common(1)[0][0] if sport_counts else 'N/A'
        
        # Alerts per day (last 7 days)
        week_alerts = self.alerts_parser.get_alerts(time_range=168, limit=10000)
        alerts_per_day = len(week_alerts) / 7.0
        
        # Alerts by sport
        alerts_by_sport = dict(sport_counts)
        
        # Alerts by type
        type_counts = Counter(a.get('type', 'general') for a in all_alerts)
        alerts_by_type = dict(type_counts)
        
        return {
            'total_alerts': total_alerts,
            'alerts_today': alerts_today,
            'avg_confidence': round(avg_confidence, 1),
            'most_active_sport': most_active_sport,
            'alerts_per_day': round(alerts_per_day, 1),
            'alerts_by_sport': alerts_by_sport,
            'alerts_by_type': alerts_by_type
        }
    
    def get_chart_data(self) -> Dict[str, Any]:
        """
        Get data for charts
        
        Returns:
            Dictionary with chart datasets
        """
        # Get recent alerts
        alerts = self.alerts_parser.get_alerts(time_range=168, limit=10000)
        
        # Alerts over time (last 7 days)
        alerts_by_date = defaultdict(int)
        now = datetime.now()
        
        for alert in alerts:
            try:
                alert_date = datetime.fromisoformat(alert['timestamp']).date()
                alerts_by_date[alert_date.isoformat()] += 1
            except:
                pass
        
        # Fill in missing dates
        dates = []
        counts = []
        for i in range(6, -1, -1):
            date = (now - timedelta(days=i)).date()
            date_str = date.isoformat()
            dates.append(date_str)
            counts.append(alerts_by_date.get(date_str, 0))
        
        # Alerts by sport
        sport_counts = Counter(a.get('sport', 'unknown') for a in alerts)
        sports = list(sport_counts.keys())
        sport_values = [sport_counts[s] for s in sports]
        
        # Confidence distribution
        confidence_buckets = defaultdict(int)
        for alert in alerts:
            conf = alert.get('confidence', 0)
            bucket = int(conf // 10) * 10
            confidence_buckets[bucket] += 1
        
        conf_labels = [f'{i}-{i+10}%' for i in range(0, 100, 10)]
        conf_values = [confidence_buckets.get(i, 0) for i in range(0, 100, 10)]
        
        # Alerts by day of week
        day_counts = defaultdict(int)
        for alert in alerts:
            try:
                alert_date = datetime.fromisoformat(alert['timestamp'])
                day_name = alert_date.strftime('%A')
                day_counts[day_name] += 1
            except:
                pass
        
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_values = [day_counts.get(day, 0) for day in days_order]
        
        return {
            'alerts_over_time': {
                'labels': dates,
                'data': counts
            },
            'alerts_by_sport': {
                'labels': sports,
                'data': sport_values
            },
            'confidence_distribution': {
                'labels': conf_labels,
                'data': conf_values
            },
            'alerts_by_day': {
                'labels': days_order,
                'data': day_values
            }
        }
    
    def get_alert_summary(
        self,
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """
        Get summary statistics for a date range
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            
        Returns:
            Summary statistics
        """
        alerts = self.alerts_parser.get_alerts(limit=10000)
        
        # Apply date filters
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            alerts = [a for a in alerts 
                     if datetime.fromisoformat(a['timestamp']) >= start_dt]
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            alerts = [a for a in alerts 
                     if datetime.fromisoformat(a['timestamp']) <= end_dt]
        
        # Calculate statistics
        total = len(alerts)
        
        by_sport = Counter(a.get('sport', 'unknown') for a in alerts)
        by_league = Counter(a.get('league', 'UNKNOWN') for a in alerts)
        by_type = Counter(a.get('type', 'general') for a in alerts)
        
        avg_confidence = sum(a.get('confidence', 0) for a in alerts) / max(total, 1)
        
        return {
            'total_alerts': total,
            'by_sport': dict(by_sport),
            'by_league': dict(by_league),
            'by_type': dict(by_type),
            'average_confidence': round(avg_confidence, 1)
        }
