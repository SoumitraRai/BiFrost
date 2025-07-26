#!/usr/bin/env python3
"""
mitmproxy Certificate Installer for Linux
This script helps install the mitmproxy CA certificate into the system trust store
and various browsers on Linux systems.
"""

import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path

def run_command(command, description=None):
    """Run a shell command and return the result"""
    if description:
        print(f"{description}...")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Error: {e.stderr}"

def detect_distro():
    """Detect the Linux distribution"""
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("ID="):
                    return line.split("=")[1].strip().strip('"')
    
    # Try to use lsb_release
    success, output = run_command("lsb_release -si", "Detecting distribution")
    if success:
        return output.strip().lower()
    
    return None

def get_cert_dir():
    """Get the mitmproxy certificate directory"""
    # Default location is ~/.mitmproxy
    home_dir = os.path.expanduser("~")
    default_cert_dir = os.path.join(home_dir, ".mitmproxy")
    
    # Check if we're in the BiFrost environment
    current_dir = os.getcwd()
    bifrost_cert_dir = os.path.join(current_dir, "certs")
    
    if os.path.exists(bifrost_cert_dir) and os.path.isfile(os.path.join(bifrost_cert_dir, "mitmproxy-ca-cert.pem")):
        return bifrost_cert_dir
    elif os.path.exists(default_cert_dir) and os.path.isfile(os.path.join(default_cert_dir, "mitmproxy-ca-cert.pem")):
        return default_cert_dir
    else:
        return None

def install_for_system(cert_dir, distro):
    """Install certificate for the system trust store"""
    cert_path = os.path.join(cert_dir, "mitmproxy-ca-cert.pem")
    
    if not os.path.exists(cert_path):
        print(f"❌ Certificate not found at {cert_path}")
        return False
    
    # Handle different distributions
    if distro in ["ubuntu", "debian", "linuxmint", "pop"]:
        # Debian/Ubuntu method
        success, output = run_command(f"sudo cp {cert_path} /usr/local/share/ca-certificates/mitmproxy-ca.crt", 
                                     "Copying certificate to system directory")
        if not success:
            print(f"❌ Failed to copy certificate: {output}")
            return False
        
        success, output = run_command("sudo update-ca-certificates", 
                                     "Updating system CA certificates")
        if not success:
            print(f"❌ Failed to update CA certificates: {output}")
            return False
            
    elif distro in ["fedora", "centos", "rhel"]:
        # Fedora/RHEL method
        success, output = run_command(f"sudo cp {cert_path} /etc/pki/ca-trust/source/anchors/mitmproxy-ca.pem",
                                     "Copying certificate to system directory")
        if not success:
            print(f"❌ Failed to copy certificate: {output}")
            return False
            
        success, output = run_command("sudo update-ca-trust extract",
                                     "Updating system CA certificates")
        if not success:
            print(f"❌ Failed to update CA certificates: {output}")
            return False
            
    elif distro in ["arch", "manjaro", "endeavouros"]:
        # Arch method
        success, output = run_command(f"sudo cp {cert_path} /etc/ca-certificates/trust-source/anchors/mitmproxy-ca.pem",
                                     "Copying certificate to system directory")
        if not success:
            print(f"❌ Failed to copy certificate: {output}")
            return False
            
        success, output = run_command("sudo trust extract-compat",
                                     "Updating system CA certificates")
        if not success:
            print(f"❌ Failed to update CA certificates: {output}")
            return False
            
    else:
        print(f"⚠️ Unsupported distribution: {distro}")
        print("Please refer to your distribution's documentation on how to install CA certificates.")
        return False
        
    print("✅ Certificate installed in system trust store")
    return True

def install_for_firefox():
    """Install certificate for Firefox"""
    # Find Firefox profiles directory
    home_dir = os.path.expanduser("~")
    firefox_dir = os.path.join(home_dir, ".mozilla", "firefox")
    
    if not os.path.exists(firefox_dir):
        print("❌ Firefox profiles directory not found")
        return False
        
    # Read profiles.ini to find profile directories
    profiles_ini = os.path.join(firefox_dir, "profiles.ini")
    if not os.path.exists(profiles_ini):
        print("❌ Firefox profiles.ini not found")
        return False
        
    profile_dirs = []
    profile_path = None
    with open(profiles_ini, 'r') as f:
        for line in f:
            if line.startswith("Path="):
                profile_path = line.split("=")[1].strip()
                profile_dirs.append(profile_path)
                
    if not profile_dirs:
        print("❌ No Firefox profiles found")
        return False
        
    # Get certificate directory
    cert_dir = get_cert_dir()
    if not cert_dir:
        print("❌ mitmproxy certificate directory not found")
        return False
        
    cert_path = os.path.join(cert_dir, "mitmproxy-ca-cert.pem")
    
    print("\nTo install the certificate in Firefox, you need to do it manually:")
    print("1. Open Firefox")
    print("2. Go to Settings (≡) > Privacy & Security > Certificates > View Certificates")
    print("3. Go to 'Authorities' tab")
    print("4. Click 'Import...' and select the certificate file:")
    print(f"   {cert_path}")
    print("5. Check 'Trust this CA to identify websites' and click OK")
    
    return True

def main():
    print("mitmproxy Certificate Installer for Linux")
    print("========================================")
    
    # Find certificate directory
    cert_dir = get_cert_dir()
    if not cert_dir:
        print("❌ mitmproxy certificate directory not found.")
        print("Run mitmproxy at least once to generate certificates.")
        sys.exit(1)
    else:
        print(f"✅ Found certificate directory at: {cert_dir}")
    
    # Detect Linux distribution
    distro = detect_distro()
    if not distro:
        print("❌ Could not detect Linux distribution")
        sys.exit(1)
    else:
        print(f"✅ Detected distribution: {distro}")
    
    # Install for system
    print("\n[1/2] Installing certificate for system trust store")
    install_for_system(cert_dir, distro)
    
    # Install for Firefox
    print("\n[2/2] Installing certificate for Firefox")
    install_for_firefox()
    
    print("\n🎉 Certificate installation process completed!")
    print("You may need to restart your browser or applications to use the new certificate.")
    print("For Chrome-based browsers, they typically use the system certificate store.")

if __name__ == "__main__":
    # Check if running as root (recommended for system-wide installation)
    if os.geteuid() == 0:
        print("Warning: Running this script as root. This is fine for system certificate installation.")
    
    main()
