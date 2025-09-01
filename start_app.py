#!/usr/bin/env python3
"""
Screenwrite App Startup Script
Starts all three services concurrently:
1. Backend API server (uvicorn on port 8001)
2. Video render service (tsx videorender.ts)
3. Frontend dev server (npm run dev)
"""

import subprocess
import os
import sys
import time
import signal
import threading
from queue import Queue, Empty
import atexit

# ANSI color codes for terminal output
class Colors:
    RED = '\033[91m'      # Backend
    GREEN = '\033[92m'    # Video render
    BLUE = '\033[94m'     # Frontend
    YELLOW = '\033[93m'   # System messages
    PURPLE = '\033[95m'   # Errors
    CYAN = '\033[96m'     # Info
    WHITE = '\033[97m'    # Default
    RESET = '\033[0m'     # Reset color

def colored_print(text, color_code):
    """Print colored text to terminal"""
    print(f"{color_code}{text}{Colors.RESET}")

def print_banner():
    """Print startup banner"""
    colored_print("=" * 60, Colors.CYAN)
    colored_print("🎬 SCREENWRITE APP LAUNCHER", Colors.CYAN)
    colored_print("=" * 60, Colors.CYAN)
    colored_print("Starting all services...", Colors.WHITE)
    print()

class ServiceManager:
    def __init__(self):
        self.processes = []
        self.output_queue = Queue()
        self.running = True
        
        # Register cleanup on exit
        atexit.register(self.cleanup)
        
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        colored_print("\n🛑 Shutting down all services...", Colors.YELLOW)
        self.running = False
        self.cleanup()
        sys.exit(0)
        
    def cleanup(self):
        """Clean up all processes"""
        for process in self.processes:
            if process.poll() is None:  # Process still running
                try:
                    colored_print(f"🔄 Terminating process {process.pid}...", Colors.YELLOW)
                    process.terminate()
                    # Wait up to 3 seconds for graceful shutdown
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        colored_print(f"⚡ Force killing process {process.pid}...", Colors.PURPLE)
                        process.kill()
                except Exception as e:
                    colored_print(f"❌ Error stopping process: {e}", Colors.PURPLE)
    
    def run_service(self, name, command, cwd, color_code):
        """Run a service and capture its output"""
        try:
            colored_print(f"🚀 Starting {name}...", Colors.YELLOW)
            colored_print(f"📁 Working directory: {cwd}", Colors.WHITE)
            colored_print(f"💻 Command: {command}", Colors.WHITE)
            print()
            
            # Start the process
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                preexec_fn=os.setsid  # Create new process group for better cleanup
            )
            
            self.processes.append(process)
            
            # Read output line by line and queue it
            def read_output():
                while self.running and process.poll() is None:
                    try:
                        output = process.stdout.readline()
                        if output:
                            self.output_queue.put((name, output.rstrip(), color_code))
                    except Exception as e:
                        self.output_queue.put((name, f"Output read error: {str(e)}", Colors.PURPLE))
                        break
                
                # Process finished
                rc = process.poll()
                if rc is not None and rc != 0:
                    self.output_queue.put((name, f"⚠️ Process exited with code {rc}", Colors.PURPLE))
                elif rc == 0:
                    self.output_queue.put((name, f"✅ Process completed successfully", color_code))
            
            # Start output reading thread
            output_thread = threading.Thread(target=read_output, daemon=True)
            output_thread.start()
            
            return process
            
        except Exception as e:
            colored_print(f"❌ Failed to start {name}: {str(e)}", Colors.PURPLE)
            return None
    
    def output_handler(self):
        """Handle output from all services"""
        while self.running:
            try:
                name, message, color_code = self.output_queue.get(timeout=0.1)
                timestamp = time.strftime("%H:%M:%S")
                colored_print(f"[{timestamp}] [{name:12}] {message}", color_code)
                self.output_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                colored_print(f"Output handler error: {e}", Colors.PURPLE)
                break
    
    def start_all_services(self):
        """Start all three services"""
        # Get the project root directory
        project_root = "/home/idrees-mustafa/Dev/screenwrite"
        backend_dir = os.path.join(project_root, "backend")
        
        # Check if directories exist
        if not os.path.exists(project_root):
            colored_print(f"❌ Project directory not found: {project_root}", Colors.PURPLE)
            return False
            
        if not os.path.exists(backend_dir):
            colored_print(f"❌ Backend directory not found: {backend_dir}", Colors.PURPLE)
            return False
        
        print_banner()
        
        # Start output handler in separate thread
        output_thread = threading.Thread(target=self.output_handler, daemon=True)
        output_thread.start()
        
        # Service configurations
        services = [
            {
                "name": "Backend API",
                "command": "uv run uvicorn main:app --reload --host 0.0.0.0 --port 8001",
                "cwd": backend_dir,
                "color": Colors.RED
            },
            {
                "name": "Video Render",
                "command": "npx tsx app/videorender/videorender.ts",
                "cwd": project_root,
                "color": Colors.GREEN
            },
            {
                "name": "Frontend Dev",
                "command": "npm run dev",
                "cwd": project_root,
                "color": Colors.BLUE
            }
        ]
        
        # Start all services
        started_services = 0
        for service in services:
            process = self.run_service(
                service["name"],
                service["command"],
                service["cwd"],
                service["color"]
            )
            if process:
                started_services += 1
                time.sleep(1)  # Small delay between starting services
        
        if started_services == 0:
            colored_print("❌ Failed to start any services", Colors.PURPLE)
            return False
        
        colored_print(f"✅ Started {started_services}/{len(services)} services", Colors.CYAN)
        colored_print("", Colors.WHITE)
        colored_print("🌐 Service URLs:", Colors.CYAN)
        colored_print("   • Backend API: http://localhost:8001", Colors.RED)
        colored_print("   • Frontend App: http://localhost:5173", Colors.BLUE)
        colored_print("   • Video Render: Background service", Colors.GREEN)
        colored_print("", Colors.WHITE)
        colored_print("💡 Press Ctrl+C to stop all services", Colors.YELLOW)
        colored_print("=" * 60, Colors.CYAN)
        print()
        
        # Keep the script running and display output
        try:
            while self.running:
                # Check if any critical process has died
                active_processes = [p for p in self.processes if p.poll() is None]
                if len(active_processes) == 0:
                    colored_print("⚠️ All services have stopped", Colors.YELLOW)
                    break
                    
                time.sleep(1)
        except KeyboardInterrupt:
            colored_print("\n🛑 Received shutdown signal", Colors.YELLOW)
        
        return True

def main():
    """Main entry point"""
    try:
        # Check if we're in the right directory
        if not os.path.exists("package.json"):
            colored_print("❌ package.json not found. Please run this script from the project root.", Colors.PURPLE)
            sys.exit(1)
        
        # Check if backend directory exists
        if not os.path.exists("backend/main.py"):
            colored_print("❌ backend/main.py not found. Please check backend setup.", Colors.PURPLE)
            sys.exit(1)
        
        # Create service manager and start services
        manager = ServiceManager()
        success = manager.start_all_services()
        
        if not success:
            colored_print("❌ Failed to start services", Colors.PURPLE)
            sys.exit(1)
            
    except Exception as e:
        colored_print(f"❌ Startup error: {e}", Colors.PURPLE)
        sys.exit(1)

if __name__ == "__main__":
    main()
