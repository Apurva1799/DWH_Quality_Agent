#!/bin/bash
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
