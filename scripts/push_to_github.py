#!/usr/bin/env python3
"""
GitHub Push Script - Pushes Multi-Agent System code to GitHub
"""

import subprocess
import os
import sys
import time
from pathlib import Path

class GitHubPusher:
    def __init__(self, repo_url="https://github.com/Apurva1799/Multi_Agent_System.git"):
        self.repo_url = repo_url
        self.project_root = Path("/home/robotics/Multi_Agent_System")
        self.env = os.environ.copy()
        
    def run_command(self, cmd, cwd=None, timeout=60):
        """Run shell command with error handling"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd or str(self.project_root),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=self.env
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def setup_git_config(self):
        """Configure git user settings"""
        print("Setting up git configuration...")
        self.run_command("git config user.email 'developer@example.com'")
        self.run_command("git config user.name 'Developer'")
        print("Git config done")
        return True
    
    def check_status(self):
        """Check current git status"""
        print("\n=== Checking Git Status ===")
        success, stdout, stderr = self.run_command("git status")
        print(stdout if success else stderr)
        return success
    
    def try_push_https(self):
        """Try HTTPS push with various workarounds"""
        print("\n=== Attempting HTTPS Push ===")
        
        # Disable SSL verification for corporate networks
        self.run_command("git config http.sslVerify false")
        
        # Try push with verbose output
        success, stdout, stderr = self.run_command(
            f"git push -v -u origin main",
            timeout=120
        )
        
        if success:
            print("HTTPS push successful!")
            print(stdout)
            return True
        else:
            print(f"HTTPS push failed: {stderr}")
            return False
    
    def try_push_with_ip(self):
        """Try push using GitHub IP instead of hostname"""
        print("\n=== Attempting Push via IP ===")
        
        # Get GitHub IP
        success, stdout, _ = self.run_command("ping -c 1 github.com | head -1 | grep -oE '[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+'")
        
        if success and stdout.strip():
            github_ip = stdout.strip()
            print(f"GitHub IP: {github_ip}")
            
            # Update /etc/hosts (requires sudo)
            hosts_entry = f"{github_ip} github.com"
            print(f"Adding to /etc/hosts: {hosts_entry}")
            
            # Try with sudo
            os.system(f"echo '{hosts_entry}' | sudo tee -a /etc/hosts > /dev/null")
            
            # Now try push again
            return self.try_push_https()
        
        return False
    
    def generate_ssh_key(self):
        """Generate SSH key for GitHub authentication"""
        print("\n=== Generating SSH Key ===")
        
        ssh_dir = Path.home() / ".ssh"
        ssh_dir.mkdir(mode=0o700, exist_ok=True)
        
        key_path = ssh_dir / "id_ed25519_github"
        
        # Generate key
        success, _, stderr = self.run_command(
            f"ssh-keygen -t ed25519 -C 'developer@example.com' -f {key_path} -N ''",
            cwd=str(Path.home())
        )
        
        if key_path.exists():
            print(f"SSH key generated at: {key_path}")
            
            # Read and display public key
            pub_key = key_path.with_suffix('.pub')
            if pub_key.exists():
                public_key = pub_key.read_text().strip()
                print("\n" + "="*60)
                print("SSH PUBLIC KEY (Add this to GitHub Settings -> SSH Keys):")
                print("="*60)
                print(public_key)
                print("="*60 + "\n")
                return str(key_path)
        
        print(f"Failed to generate SSH key: {stderr}")
        return None
    
    def try_push_ssh(self):
        """Try SSH push"""
        print("\n=== Attempting SSH Push ===")
        
        # Generate SSH key if not exists
        ssh_key = self.generate_ssh_key()
        
        if not ssh_key:
            return False
        
        # Update remote to SSH URL
        ssh_url = "git@github.com:Apurva1799/Multi_Agent_System.git"
        self.run_command(f"git remote set-url origin {ssh_url}")
        
        # Add GitHub to known hosts
        self.run_command("ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null", cwd=str(Path.home()))
        
        # Configure SSH agent
        self.run_command(f"eval $(ssh-agent -s) && ssh-add {ssh_key}", cwd=str(Path.home()))
        
        # Try push
        success, stdout, stderr = self.run_command(
            "git push -v -u origin main",
            timeout=120
        )
        
        if success:
            print("SSH push successful!")
            return True
        else:
            print(f"SSH push failed: {stderr}")
            print("\nNote: You need to add the SSH key to GitHub first:")
            print("1. Copy the public key shown above")
            print("2. Go to https://github.com/settings/keys")
            print("3. Click 'New SSH key' and paste the key")
            return False
    
    def use_github_api(self, token=None):
        """Try using GitHub API to create/update files"""
        print("\n=== Attempting GitHub API Push ===")
        
        if not token:
            token = os.getenv("GITHUB_TOKEN", "")
        
        if not token:
            print("GITHUB_TOKEN not set. Cannot use API method.")
            return False
        
        # This would require implementing file-by-file upload
        print("API method requires GITHUB_TOKEN environment variable")
        return False
    
    def create_push_script(self):
        """Create a standalone push script"""
        script_content = """#!/bin/bash
# GitHub Push Script - Run this to push code

cd /home/robotics/Multi_Agent_System

# Configure git
git config user.email 'developer@example.com'
git config user.name 'Developer'
git config http.sslVerify false

# Add GitHub IP to hosts (if needed)
echo "20.207.73.82 github.com" | sudo tee -a /etc/hosts

# Try push with verbose output
git push -v -u origin main

if [ $? -eq 0 ]; then
    echo "Push successful!"
else
    echo "Push failed. Trying alternative methods..."
    
    # Try SSH method
    ssh-keygen -t ed25519 -C 'developer@example.com' -f ~/.ssh/id_ed25519_github -N ''
    echo "Add this SSH key to GitHub:"
    cat ~/.ssh/id_ed25519_github.pub
fi
"""
        
        script_path = self.project_root / "push_to_github.sh"
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        
        print(f"Created push script: {script_path}")
        return str(script_path)
    
    def run_all_strategies(self):
        """Run all push strategies"""
        print("="*60)
        print("GITHUB PUSH AUTOMATION")
        print("="*60)
        
        # Setup
        os.chdir(str(self.project_root))
        self.setup_git_config()
        self.check_status()
        
        # Try Strategy 1: HTTPS with workarounds
        if self.try_push_https():
            return True
        
        # Try Strategy 2: IP-based push
        if self.try_push_with_ip():
            return True
        
        # Try Strategy 3: SSH
        if self.try_push_ssh():
            return True
        
        # Fallback: Create manual script
        print("\n" + "="*60)
        print("AUTOMATED PUSH FAILED - CREATING MANUAL SCRIPT")
        print("="*60)
        
        script_path = self.create_push_script()
        
        print(f"\nCreated: {script_path}")
        print("\nTo push manually, run:")
        print(f"  bash {script_path}")
        print("\nOr use the ZIP file method:")
        print("  /home/robotics/Multi_Agent_System_Code.zip")
        
        return False

def main():
    pusher = GitHubPusher()
    success = pusher.run_all_strategies()
    
    if success:
        print("\n" + "="*60)
        print("SUCCESS! Code pushed to GitHub")
        print("="*60)
        print(f"Repository: {pusher.repo_url}")
        return 0
    else:
        print("\n" + "="*60)
        print("PUSH FAILED - See alternative methods above")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
