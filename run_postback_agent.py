#!/usr/bin/env python3
"""
Simple script to run the Postback-Agent
"""

import subprocess
import sys
import os

def run_postback_agent():
    """Run the postback-agent"""
    print("🚀 Starting Postback-Agent...")
    print("=" * 50)
    
    try:
        # Set environment variables
        os.environ["PYTHONPATH"] = os.getcwd()
        
        # Run the postback agent using the new location
        result = subprocess.run([
            sys.executable, 
            "-m", "agents.postback_agent.main"
        ], check=True)
        
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running postback-agent: {e}")
        return e.returncode
    except KeyboardInterrupt:
        print("\n⏹️  Postback-agent stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_postback_agent()
    sys.exit(exit_code) 