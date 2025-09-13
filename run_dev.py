#!/usr/bin/env python3
"""
Development server with auto-restart functionality
This script watches for file changes and restarts the MCP server automatically
Use run_servers.py for production (no auto-restart)
"""

import subprocess
import sys
import time
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RestartHandler(FileSystemEventHandler):
    def __init__(self, script_path):
        self.script_path = script_path
        self.process = None
        self.start_server()
    
    def start_server(self):
        """Start the MCP server"""
        if self.process:
            print("🔄 Stopping previous server...")
            self.process.terminate()
            try:
                # Wait for graceful shutdown
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't stop gracefully
                print("⚠️  Force killing previous server...")
                self.process.kill()
                self.process.wait()
        
        # Small delay to ensure port is released
        time.sleep(0.5)
        
        print("🚀 Starting MCP server...")
        self.process = subprocess.Popen([sys.executable, self.script_path])
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
        
        # Only restart for Python files
        if event.src_path.endswith('.py'):
            print(f"📝 File changed: {event.src_path}")
            print("🔄 Restarting server...")
            self.start_server()

def main():
    script_path = Path(__file__).parent / "main.py"
    
    if not script_path.exists():
        print("❌ main.py not found!")
        sys.exit(1)
    
    print("🔧 Development mode with auto-restart enabled")
    print("📁 Watching for changes in Python files...")
    print("🛑 Press Ctrl+C to stop")
    print("-" * 50)
    
    # Set up file watcher
    event_handler = RestartHandler(script_path)
    observer = Observer()
    observer.schedule(event_handler, path=str(script_path.parent), recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        observer.stop()
        if event_handler.process:
            print("🔄 Stopping server...")
            event_handler.process.terminate()
            try:
                event_handler.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                print("⚠️  Force killing server...")
                event_handler.process.kill()
                event_handler.process.wait()
    
    observer.join()

if __name__ == "__main__":
    main()
