#!/usr/bin/env python3
"""
Quick Start Script for Sports Betting Dashboard

Launches the dashboard with a single command and opens browser automatically.
"""

import os
import sys
import time
import webbrowser
import subprocess
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed"""
    # Map import names to package names
    required_packages = {
        'flask': 'flask',
        'flask_cors': 'flask-cors',
        'yaml': 'pyyaml'
    }
    missing = []
    
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        print("❌ Missing required packages:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n📦 Installing missing packages...")
        
        # Install missing packages
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                'flask', 'flask-cors', 'pyyaml'
            ])
            print("✅ Packages installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing packages: {e}")
            print("\nPlease run manually:")
            print("  pip install flask flask-cors pyyaml")
            return False
    
    return True


def main():
    """Main entry point"""
    print("=" * 60)
    print("🎯 Sports Betting Dashboard - Quick Start")
    print("=" * 60)
    print()
    
    # Check if we're in the right directory
    if not Path('bot.py').exists():
        print("❌ Error: This script must be run from the Sport-Betting-Bot directory")
        print("   Please navigate to the repository root and try again.")
        sys.exit(1)
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    print("✅ All dependencies satisfied")
    print()
    
    # Configuration
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    
    # Dashboard URL
    url = f"http://{host}:{port}"
    
    print(f"🚀 Starting dashboard on {url}")
    print()
    print("📊 Dashboard Features:")
    print("   • Real-time alerts feed with filtering")
    print("   • Comprehensive alert history")
    print("   • Analytics dashboard with charts")
    print("   • Notification settings management")
    print()
    print("ℹ️  Press Ctrl+C to stop the dashboard")
    print()
    
    # Wait a moment then open browser
    def open_browser():
        time.sleep(1.5)
        print(f"🌐 Opening dashboard in browser: {url}")
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"⚠️  Could not open browser automatically: {e}")
            print(f"   Please open {url} manually")
    
    # Start browser opener in background
    import threading
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start Flask app
    try:
        # Change to dashboard directory
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Import and run app
        from dashboard.app import app
        app.run(host=host, port=port, debug=False)
        
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped")
        print("   Thank you for using Sports Betting Dashboard!")
    except Exception as e:
        print(f"\n❌ Error starting dashboard: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
