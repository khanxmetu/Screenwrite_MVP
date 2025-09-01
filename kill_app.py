#!/usr/bin/env python3
"""
Screenwrite App Killer Script
Kills all running services for the Screenwrite app:
1. Backend API server (uvicorn on port 8001)
2. Video render service (tsx videorender.ts)
3. Frontend dev server (npm run dev)
"""

import subprocess
import os
import sys
import time
import signal

# ANSI color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'

def colored_print(text, color_code):
    """Print colored text to terminal"""
    print(f"{color_code}{text}{Colors.RESET}")

def print_banner():
    """Print killer banner"""
    colored_print("=" * 60, Colors.RED)
    colored_print("🔥 SCREENWRITE APP KILLER", Colors.RED)
    colored_print("=" * 60, Colors.RED)
    colored_print("Searching for running services...", Colors.WHITE)
    print()

def find_processes_by_pattern(patterns):
    """Find processes matching given patterns using ps command"""
    matching_processes = []
    
    try:
        # Use ps to get all processes with full command line
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            colored_print("❌ Failed to get process list", Colors.PURPLE)
            return matching_processes
        
        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        
        for line in lines:
            parts = line.split(None, 10)  # Split into max 11 parts
            if len(parts) >= 11:
                pid = parts[1]
                command = parts[10]
                
                for pattern in patterns:
                    if pattern.lower() in command.lower():
                        matching_processes.append({
                            'pid': int(pid),
                            'command': command,
                            'pattern': pattern
                        })
                        break
                        
    except subprocess.TimeoutExpired:
        colored_print("⏱️ Timeout getting process list", Colors.PURPLE)
    except Exception as e:
        colored_print(f"❌ Error getting process list: {e}", Colors.PURPLE)
    
    return matching_processes

def kill_process_by_pid(pid, command, force=False):
    """Kill a process by PID"""
    try:
        if force:
            colored_print(f"⚡ Force killing PID {pid}: {command[:60]}...", Colors.RED)
            os.kill(pid, signal.SIGKILL)
        else:
            colored_print(f"🔄 Gracefully terminating PID {pid}: {command[:60]}...", Colors.YELLOW)
            os.kill(pid, signal.SIGTERM)
        return True
    except OSError as e:
        if e.errno == 3:  # No such process
            colored_print(f"⚠️ Process {pid} not found (already dead)", Colors.PURPLE)
        elif e.errno == 1:  # Permission denied
            colored_print(f"❌ Permission denied killing PID {pid}", Colors.PURPLE)
        else:
            colored_print(f"❌ Error killing PID {pid}: {e}", Colors.PURPLE)
        return False
    except Exception as e:
        colored_print(f"❌ Unexpected error killing PID {pid}: {e}", Colors.PURPLE)
        return False

def kill_processes_by_port(port):
    """Kill processes using a specific port"""
    try:
        # Find processes using the port with lsof
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            killed_any = False
            for pid in pids:
                try:
                    pid = int(pid.strip())
                    colored_print(f"🔫 Killing process on port {port} (PID: {pid})", Colors.RED)
                    os.kill(pid, signal.SIGTERM)
                    killed_any = True
                    time.sleep(0.5)
                    # Check if still running, force kill if needed
                    try:
                        os.kill(pid, 0)  # Check if process exists
                        colored_print(f"⚡ Force killing stubborn process (PID: {pid})", Colors.RED)
                        os.kill(pid, signal.SIGKILL)
                    except OSError:
                        pass  # Process already dead
                except ValueError:
                    continue
                except OSError as e:
                    if e.errno != 3:  # Ignore "No such process" errors
                        colored_print(f"⚠️ Could not kill PID {pid}: {e}", Colors.PURPLE)
            return killed_any
        else:
            return False
    except subprocess.TimeoutExpired:
        colored_print(f"⏱️ Timeout checking port {port}", Colors.PURPLE)
        return False
    except FileNotFoundError:
        # lsof not available, try netstat alternative
        try:
            result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if f':{port}' in line and 'LISTEN' in line:
                        # Extract PID from netstat output (format: "pid/name")
                        parts = line.split()
                        for part in parts:
                            if '/' in part and part.split('/')[0].isdigit():
                                pid = int(part.split('/')[0])
                                colored_print(f"🔫 Killing process on port {port} (PID: {pid})", Colors.RED)
                                try:
                                    os.kill(pid, signal.SIGTERM)
                                    return True
                                except OSError:
                                    pass
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            colored_print(f"⚠️ Cannot check port {port} - lsof/netstat not available", Colors.PURPLE)
            return False
    except Exception as e:
        colored_print(f"❌ Error checking port {port}: {e}", Colors.PURPLE)
        return False

def main():
    """Main killer function"""
    print_banner()
    
    killed_count = 0
    
    # Define service patterns to search for
    service_patterns = [
        "uvicorn main:app",           # Backend API
        "tsx app/videorender",        # Video render service  
        "npm run dev",               # Frontend dev server
        "vite",                      # Vite dev server (npm run dev usually starts vite)
        "tsx videorender.ts",        # Alternative video render pattern
    ]
    
    # Find matching processes
    colored_print("🔍 Searching for Screenwrite processes...", Colors.CYAN)
    matching_processes = find_processes_by_pattern(service_patterns)
    
    if not matching_processes:
        colored_print("✅ No Screenwrite processes found running", Colors.GREEN)
    else:
        colored_print(f"🎯 Found {len(matching_processes)} matching processes:", Colors.YELLOW)
        print()
        
        for proc in matching_processes:
            colored_print(f"📍 PID: {proc['pid']}", Colors.WHITE)
            colored_print(f"   Command: {proc['command'][:80]}{'...' if len(proc['command']) > 80 else ''}", Colors.WHITE)
            colored_print(f"   Pattern: {proc['pattern']}", Colors.CYAN)
            print()
        
        # Kill processes gracefully first
        colored_print("🔄 Attempting graceful termination...", Colors.YELLOW)
        for proc in matching_processes:
            if kill_process_by_pid(proc['pid'], proc['command'], force=False):
                killed_count += 1
        
        # Wait a bit for graceful shutdown
        if killed_count > 0:
            colored_print("⏱️ Waiting 3 seconds for graceful shutdown...", Colors.YELLOW)
            time.sleep(3)
        
        # Check for stubborn processes and force kill them
        colored_print("🔍 Checking for stubborn processes...", Colors.CYAN)
        remaining_processes = find_processes_by_pattern(service_patterns)
        
        if remaining_processes:
            colored_print(f"⚡ Force killing {len(remaining_processes)} stubborn processes...", Colors.RED)
            for proc in remaining_processes:
                kill_process_by_pid(proc['pid'], proc['command'], force=True)
                killed_count += 1
    
    # Also check specific ports
    colored_print("🔍 Checking specific ports...", Colors.CYAN)
    ports_to_check = [8001, 5173, 3000, 4173]  # Common ports for the services
    
    for port in ports_to_check:
        if kill_processes_by_port(port):
            killed_count += 1
    
    print()
    colored_print("=" * 60, Colors.CYAN)
    
    if killed_count > 0:
        colored_print(f"✅ Successfully terminated {killed_count} processes", Colors.GREEN)
        colored_print("🎉 All Screenwrite services have been stopped", Colors.GREEN)
    else:
        colored_print("ℹ️ No processes were terminated (none were running)", Colors.CYAN)
    
    colored_print("=" * 60, Colors.CYAN)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        colored_print("\n⚠️ Kill operation interrupted", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        colored_print(f"\n❌ Error during kill operation: {e}", Colors.PURPLE)
        sys.exit(1)
