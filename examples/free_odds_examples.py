#!/usr/bin/env python3
"""
Example: Using Free Odds Scraping
Demonstrates how to use the new free odds integration
NO API KEYS REQUIRED!
"""

import sys
sys.path.insert(0, '/home/runner/work/Sport-Betting-Bot/Sport-Betting-Bot')

from sportsbooks.book_manager import SportsbookManager
from sportsbooks.espn_client import ESPNClient
from sportsbooks.odds_scraper import OddsScraper

def example_1_basic_odds_scraping():
    """Example 1: Basic odds scraping"""
    print("=" * 70)
    print("EXAMPLE 1: Basic Odds Scraping")
    print("=" * 70)
    
    # Create odds scraper
    scraper = OddsScraper(
        rate_limit_seconds=5,      # Wait 5 seconds between requests
        cache_duration_minutes=2    # Cache odds for 2 minutes
    )
    
    # Fetch odds for an NBA game
    print("\nFetching odds for NBA game...")
    odds = scraper.fetch_odds('nba', 'game-123')
    
    if odds:
        print(f"\n✓ Retrieved odds from {len(odds)} sportsbooks:")
        for book_name, book_odds in odds.items():
            print(f"\n  {book_name.upper()}:")
            print(f"    Moneyline: Home {book_odds['moneyline']['home']}, "
                  f"Away {book_odds['moneyline']['away']}")
            print(f"    Spread: Home {book_odds['spread']['home']}, "
                  f"Away {book_odds['spread']['away']}")
            print(f"    Total: O/U {book_odds['total']['over']}")
    
    scraper.close()

def example_2_sportsbook_manager():
    """Example 2: Using SportsbookManager with free odds"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: SportsbookManager Integration")
    print("=" * 70)
    
    # Enable sportsbooks
    enabled_books = {
        'fanduel': True,
        'draftkings': True,
        'betmgm': True,
        'caesars': True,
        'pointsbet': True
    }
    
    # Initialize with free odds scraping
    manager = SportsbookManager(enabled_books, use_free_odds=True)
    
    print("\n✓ SportsbookManager initialized with FREE odds scraping")
    print(f"  Available books: {', '.join(manager.get_available_books())}")
    
    # Get odds from all books
    print("\nFetching odds from all sportsbooks...")
    all_odds = manager.get_all_odds('nba', 'game-456')
    
    if all_odds:
        print(f"✓ Retrieved odds from {len(all_odds)} books")
        
        # Find best odds for home moneyline
        best = manager.find_best_odds('nba', 'game-456', 'moneyline', 'home')
        if best:
            book, odds = best
            print(f"\n✓ Best home moneyline: {book.upper()} at {odds:+d}")

def example_3_espn_api():
    """Example 3: Using ESPN free API"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: ESPN Free API")
    print("=" * 70)
    
    client = ESPNClient()
    
    print("\n✓ ESPN client initialized (NO API KEY REQUIRED)")
    
    # Try to fetch NBA scoreboard
    print("\nFetching NBA scoreboard...")
    scoreboard = client.get_scoreboard('nba')
    
    if scoreboard and 'events' in scoreboard:
        games = scoreboard['events']
        print(f"✓ Found {len(games)} NBA games today:")
        
        for game in games[:3]:  # Show first 3 games
            if 'name' in game:
                print(f"  - {game['name']}")
    else:
        print("  (No games available or off-season)")
    
    client.close()

def example_4_comparing_odds():
    """Example 4: Comparing odds across sportsbooks"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Comparing Odds Across Sportsbooks")
    print("=" * 70)
    
    scraper = OddsScraper()
    odds = scraper.fetch_odds('nba', 'test-game')
    
    if odds:
        print("\nMoneyline comparison for home team:")
        print("-" * 50)
        
        # Sort by best home moneyline odds
        sorted_books = sorted(
            odds.items(),
            key=lambda x: x[1]['moneyline']['home'],
            reverse=True
        )
        
        for book, book_odds in sorted_books:
            home_ml = book_odds['moneyline']['home']
            print(f"  {book.upper():15s}: {home_ml:+4d}")
        
        # Show difference between best and worst
        best = sorted_books[0][1]['moneyline']['home']
        worst = sorted_books[-1][1]['moneyline']['home']
        diff = abs(best - worst)
        print(f"\n  Difference: {diff} points")
        print(f"  Best book: {sorted_books[0][0].upper()}")
    
    scraper.close()

def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("FREE ODDS SCRAPING EXAMPLES")
    print("NO API KEYS REQUIRED!")
    print("=" * 70)
    
    try:
        example_1_basic_odds_scraping()
        example_2_sportsbook_manager()
        example_3_espn_api()
        example_4_comparing_odds()
        
        print("\n" + "=" * 70)
        print("✓ All examples completed successfully!")
        print("=" * 70)
        print("\nKey Benefits:")
        print("  ✓ $0/month cost (no API subscriptions)")
        print("  ✓ Real-time odds from multiple sportsbooks")
        print("  ✓ No API keys or authentication required")
        print("  ✓ Easy to use and integrate")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
