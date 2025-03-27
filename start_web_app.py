"""Launcher script for ES Analysis Web Application"""

import os
import sys
import time
import threading
import webbrowser

def open_browser():
    """Open browser after a short delay to ensure server is running"""
    time.sleep(2)  # Give the server 2 seconds to start
    url = 'http://localhost:5000'
    webbrowser.open(url)
    print(f"Opening browser at {url}")

def main():
    """
    Main function to launch the web application and open browser
    If Flask is not installed, guides the user to install requirements
    """
    try:
        from flask import Flask
        print("Starting Earned Schedule & Critical Path Analysis web server...")
        print("\nThis application provides a web interface for:")  
        print("  • Uploading project Excel files")
        print("  • Running ES and path-specific analysis")
        print("  • Visualizing project performance")  
        print("  • Identifying the true longest/controlling path")
        print("\nThe browser will open automatically in a few seconds.")
        
        # Start browser in a separate thread
        threading.Thread(target=open_browser).start()
        
        # Import and run the web application
        from web_app import app
        app.run(debug=False, port=5000)
        
    except ImportError:
        print("\nERROR: Required dependencies not found.")
        print("Please install the required packages by running:")
        print("\n    pip install -r requirements.txt\n")
        choice = input("Would you like to install the requirements now? (y/n): ").strip().lower()
        if choice == 'y':
            import subprocess
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
                print("\nDependencies installed successfully. Restarting application...")
                os.execv(sys.executable, [sys.executable] + sys.argv)
            except subprocess.CalledProcessError:
                print("\nFailed to install dependencies. Please install them manually.")
                sys.exit(1)

if __name__ == "__main__":
    main()
