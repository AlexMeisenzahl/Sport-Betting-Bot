#!/usr/bin/env python3
"""
Test script for notification system

Tests all notification channels and validates configuration.
"""

import yaml
import sys
from utils.notifier import Notifier
from utils.logger import setup_logger


def main():
    """Test notification system"""
    print("=" * 60)
    print("Sports Betting Bot - Notification System Test")
    print("=" * 60)
    print()
    
    # Load config
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        print("✓ Configuration loaded successfully")
    except FileNotFoundError:
        print("✗ ERROR: config.yaml not found")
        print("  Copy config.example.yaml to config.yaml first:")
        print("  cp config.example.yaml config.yaml")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"✗ ERROR: Invalid YAML in config.yaml: {e}")
        sys.exit(1)
    
    print()
    
    # Initialize logger
    logger = setup_logger("notification_test")
    print("✓ Logger initialized")
    print()
    
    # Initialize notifier
    try:
        notifier = Notifier(config, logger)
        print("✓ Notifier initialized successfully")
    except Exception as e:
        print(f"✗ ERROR: Failed to initialize notifier: {e}")
        sys.exit(1)
    
    print()
    print("-" * 60)
    print("Notification Channel Status:")
    print("-" * 60)
    
    stats = notifier.get_statistics()
    channels = stats['channels_enabled']
    
    print(f"  Desktop:  {'✓ Enabled' if channels['desktop'] else '✗ Disabled'}")
    print(f"  Email:    {'✓ Enabled' if channels['email'] else '✗ Disabled'}")
    print(f"  Telegram: {'✓ Enabled' if channels['telegram'] else '✗ Disabled'}")
    print(f"  Sound:    {'✓ Enabled' if channels['sound'] else '✗ Disabled'}")
    
    print()
    print("-" * 60)
    print("Testing Enabled Channels:")
    print("-" * 60)
    print()
    
    # Test notifications
    results = notifier.test_notifications()
    
    if results:
        print("Test Results:")
        for channel, success in results.items():
            status = "✓ SUCCESS" if success else "✗ FAILED"
            print(f"  {channel.capitalize()}: {status}")
    else:
        print("No notifications sent (all channels disabled or quiet hours active)")
    
    print()
    print("-" * 60)
    print("Configuration Details:")
    print("-" * 60)
    
    # Rate limiting
    rate_limit = stats['rate_limiting']
    print(f"  Rate Limiting: {'✓ Enabled' if rate_limit['enabled'] else '✗ Disabled'}")
    
    # Quiet hours
    quiet_hours = stats['quiet_hours']
    print(f"  Quiet Hours:   {'✓ Enabled' if quiet_hours['enabled'] else '✗ Disabled'}")
    if quiet_hours['enabled']:
        print(f"    Currently:   {'🔕 Quiet' if quiet_hours['currently_quiet'] else '🔔 Active'}")
    
    print()
    print("-" * 60)
    print("Specific Event Tests:")
    print("-" * 60)
    print()
    
    # Test specific notification types
    if any(results.values()):
        print("Testing opportunity notification...")
        notifier.alert_opportunity_found("NBA", "Lakers vs Celtics", 7.5)
        print("  ✓ Sent")
        
        print()
        print("Testing trade execution notification...")
        notifier.alert_trade_executed("NFL", "Chiefs vs Bills", 50.0, 2.5)
        print("  ✓ Sent")
        
        print()
        print("Testing error notification...")
        notifier.alert_error("Test Error", "This is a test error notification")
        print("  ✓ Sent")
    
    print()
    print("=" * 60)
    print("Notification System Test Complete")
    print("=" * 60)
    
    # Show final stats
    final_stats = notifier.get_statistics()
    print(f"\nTotal notifications sent: {final_stats['total_notifications']}")
    
    if not any(channels.values()):
        print("\n⚠️  WARNING: All notification channels are disabled!")
        print("   Enable at least one channel in config.yaml to receive notifications.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
