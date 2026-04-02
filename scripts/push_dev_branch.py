#!/usr/bin/env python3
"""
GitHub Push Script - Push to DEV branch
"""

import subprocess
import os
import sys
from pathlib import Path

class GitHubDevPusher:
    def __init__(self, repo_url="https://github.com/Apurva1799/Multi_Agent_System.git"):
        self.repo_url = repo_url
        self.project_root = Path("/home/robotics/Multi_Agent_System")
        self.env = os.environ.copy()
        # Disable SSL verification
        self.env['GIT_SSL_NO_VERIFY'] = '1'
        
    def run_command(self, cmd, cwd=None, timeout=120):
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
    
    def setup_git(self):
        """Configure git settings"""
        print("Setting up git configuration...")
        self.run_command("git config user.email 'developer@example.com'")
        self.run_command("git config user.name 'Developer'")
        self.run_command("git config http.sslVerify false")
        self.run_command("git config http.postBuffer 524288000")
        print("Git config done")
        return True
    
    def switch_to_dev_branch(self):
        """Create and switch to dev branch"""
        print("\n=== Switching to DEV branch ===")
        
        # Check if dev branch exists locally
        success, stdout, _ = self.run_command("git branch --list dev")
        
        if "dev" in stdout:
            print("Dev branch exists locally, checking out...")
            self.run_command("git checkout dev")
        else:
            print("Creating new dev branch...")
            self.run_command("git checkout -b dev")
        
        # Verify current branch
        success, stdout, _ = self.run_command("git branch --show-current")
        current_branch = stdout.strip()
        print(f"Current branch: {current_branch}")
        
        return current_branch == "dev"
    
    def push_to_dev(self):
        """Push to dev branch on GitHub"""
        print("\n=== Pushing to DEV branch ===")
        print(f"Remote URL: {self.repo_url}")
        
        # Try to push dev branch
        success, stdout, stderr = self.run_command(
            f"git push -v -u origin dev",
            timeout=180
        )
        
        if success:
            print("\n" + "="*60)
            print("SUCCESS! Code pushed to DEV branch")
            print("="*60)
            print(f"Repository: {self.repo_url}")
            print(f"Branch: dev")
            print("\nYour code is now on GitHub!")
            return True
        else:
            print(f"\nPush output:\n{stdout}\n{stderr}")
            
            # Check if it's an authentication issue
            if "Authentication failed" in stderr or "403" in stderr:
                print("\nAuthentication required. You need to provide credentials.")
                return self.push_with_token()
            
            # Check if dev branch doesn't exist on remote
            if "couldn't find remote ref" in stderr.lower() or "fetch first" in stderr.lower():
                print("\nAttempting force push to create dev branch...")
                success, stdout, stderr = self.run_command(
                    "git push --force -u origin dev",
                    timeout=180
                )
                if success:
                    print("\n" + "="*60)
                    print("SUCCESS! Code pushed to DEV branch (force)")
                    print("="*60)
                    return True
                else:
                    print(f"Force push also failed: {stderr}")
            
            return False
    
    def push_with_token(self):
        """Push using GitHub token if available"""
        token = os.getenv("GITHUB_TOKEN", "")
        
        if not token:
            print("\nNo GITHUB_TOKEN found in environment.")
            print("To push with token, set it first:")
            print("  export GITHUB_TOKEN='your_token_here'")
            return False
        
        # Update remote URL with token
        token_url = f"https://{token}@github.com/Apurva1799/Multi_Agent_System.git"
        self.run_command(f"git remote set-url origin {token_url}")
        
        success, stdout, stderr = self.run_command(
            "git push -v -u origin dev",
            timeout=180
        )
        
        # Reset URL back for security
        self.run_command(f"git remote set-url origin {self.repo_url}")
        
        if success:
            print("\n" + "="*60)
            print("SUCCESS! Code pushed with token")
            print("="*60)
            return True
        else:
            print(f"Token push failed: {stderr}")
            return False
    
    def verify_push(self):
        """Verify the push was successful"""
        print("\n=== Verifying Push ===")
        
        success, stdout, _ = self.run_command("git log --oneline -3")
        print(f"\nRecent commits:\n{stdout}")
        
        success, stdout, _ = self.run_command("git branch -vv")
        print(f"\nBranch status:\n{stdout}")
        
        return True
    
    def run(self):
        """Main execution"""
        print("="*60)
        print("GITHUB DEV BRANCH PUSH")
        print("="*60)
        
        os.chdir(str(self.project_root))
        
        # Setup git
        self.setup_git()
        
        # Switch to dev branch
        if not self.switch_to_dev_branch():
            print("ERROR: Failed to switch to dev branch")
            return False
        
        # Push to dev
        if self.push_to_dev():
            self.verify_push()
            return True
        else:
            print("\n" + "="*60)
            print("PUSH FAILED")
            print("="*60)
            print("\nAlternative: Use the ZIP file at:")
            print("  /home/robotics/Multi_Agent_System_Code.zip")
            print("\nUpload this to GitHub manually:")
            print("  https://github.com/Apurva1799/Multi_Agent_System/upload")
            return False

def main():
    pusher = GitHubDevPusher()
    success = pusher.run()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
