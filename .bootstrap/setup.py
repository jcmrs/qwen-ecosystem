#!/usr/bin/env python3
"""
Bootstrap Setup Script
Use this script to set up the complete UTCP-based ecosystem
"""

import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                           capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error installing dependencies: {result.stderr}")
        return False
    print("✓ Dependencies installed")
    return True

def setup_configuration():
    """Set up basic configuration"""
    print("Setting up configuration...")
    
    # Create config directory if it doesn't exist
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # Create a basic configuration file
    config_content = """[system]
name = UTCP Research and Knowledge Distillation Ecosystem
version = 1.0.0

[research]
materials_dir = data/research/materials
findings_dir = data/research/findings
discovery_depth = 3
auto_verify_sources = true

[distillation]
knowledge_dir = data/distillation/knowledge
wisdom_dir = data/distillation/wisdom
human_validation_required = true
confidence_threshold = 0.8

[graph]
database_type = in_memory
storage_path = data/graph_data

[utcp]
discovery_interval = 3600
retry_attempts = 3
"""
    
    with open(config_dir / "app_config.ini", "w", encoding='utf-8') as f:
        f.write(config_content)
    
    print("✓ Configuration set up")
    return True

def setup_directories():
    """Set up required directories"""
    print("Setting up directories...")
    
    dirs_to_create = [
        "data",
        "data/research/materials",
        "data/research/findings", 
        "data/distillation/knowledge",
        "data/distillation/wisdom",
        "data/graph_data",
        "logs",
        "temp"
    ]
    
    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✓ Directories set up")
    return True

def verify_setup():
    """Verify that setup was successful"""
    print("Verifying setup...")
    
    # Check if key files exist
    essential_files = [
        "requirements.txt",
        "main.py",
        "src/graph/graph_db.py",
        "utcp_implementation/domain_profiles.py"
    ]
    
    missing_files = []
    for file_path in essential_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing essential files: {missing_files}")
        return False
    
    print("✓ Setup verification passed")
    return True

def main():
    """Main setup function"""
    print("Starting UTCP-Based Ecosystem Bootstrap Setup...")
    print("=" * 50)
    
    success = True
    
    # Run setup steps
    success &= setup_directories()
    success &= setup_configuration()
    success &= install_dependencies()
    success &= verify_setup()
    
    print("=" * 50)
    if success:
        print("🎉 Bootstrap setup completed successfully!")
        print("\nTo start the ecosystem, run: python main.py")
    else:
        print("❌ Bootstrap setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
