#!/usr/bin/env python3
"""Test script to check if we can open the personal KeePass database"""

import sys
import getpass
from pykeepass import PyKeePass

def test_keepass_access(db_path, password=None):
    """Test accessing a KeePass database"""
    try:
        if not password:
            password = getpass.getpass(f"Enter master password for {db_path}: ")
        
        print(f"Attempting to open KeePass database: {db_path}")
        kp = PyKeePass(db_path, password=password)
        
        print(f"✓ Successfully opened database!")
        print(f"  Database version: {kp.version}")
        print(f"  Number of entries: {len(kp.entries)}")
        print(f"  Number of groups: {len(kp.groups)}")
        
        # List root groups
        print("\nRoot groups:")
        for group in kp.root_group.subgroups:
            print(f"  - {group.name}")
        
        # Show first few entry titles (not passwords)
        print("\nFirst 5 entries:")
        for i, entry in enumerate(kp.entries[:5]):
            print(f"  {i+1}. {entry.title} (in {entry.path})")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to open database: {e}")
        return False

if __name__ == "__main__":
    db_path = "/Users/alf/Documents/1_per/keepass/aLFpwnDB.kdbx"
    
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    test_keepass_access(db_path)