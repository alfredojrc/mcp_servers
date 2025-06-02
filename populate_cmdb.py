#!/usr/bin/env python3
"""
Populate CMDB with services from ports.md
"""
import csv
import re
from pathlib import Path

def parse_ports_md():
    """Parse ports.md and extract service information"""
    services = []
    
    with open('ports.md', 'r') as f:
        content = f.read()
    
    # Define sections to parse
    sections = [
        ('MCP Services', 'mcp', 'localhost'),
        ('Monitoring Services', 'monitoring', 'localhost'),
        ('N8N Workflow Services', 'n8n', 'localhost'),
        ('Freqtrade Services', 'freqtrade', 'localhost'),
        ('Hawkeye Trading Platform', 'hawkeye', 'localhost'),
        ('GeminiFreq Trading Platform', 'geminifreq', 'localhost'),
        ('ClaudeFreq Trading Platform', 'claudefreq', 'localhost')
    ]
    
    for section_name, service_type, default_host in sections:
        # Find section in markdown
        section_pattern = rf'## {section_name}.*?\n\n(.*?)(?=\n## |\Z)'
        section_match = re.search(section_pattern, content, re.DOTALL)
        
        if section_match:
            section_content = section_match.group(1)
            
            # Parse table rows
            table_pattern = r'\|\s*`?([^`|]+)`?\s*\|[^|]+\|\s*`?(\d+)->(\d+)`?.*?\|\s*([^|]+)\s*\|'
            
            for match in re.finditer(table_pattern, section_content):
                container_name = match.group(1).strip()
                host_port = match.group(2).strip()
                container_port = match.group(3).strip()
                notes = match.group(4).strip()
                
                # Skip header rows
                if container_name.lower() == 'container name':
                    continue
                
                service = {
                    'hostname': container_name,
                    'ip_address': f'{default_host}:{host_port}',
                    'os_type': 'Docker',
                    'os_version': 'Container',
                    'services': f'{service_type},{notes[:50]}',  # Truncate long notes
                    'path': f'/container/{container_name}',
                    'user': 'docker',
                    'ssh_access_notes': f'Port mapping: {host_port}->{container_port}'
                }
                services.append(service)
    
    return services

def update_cmdb_csv(services):
    """Update the CMDB CSV file with new services"""
    cmdb_path = Path('12_cmdb_mcp/data/cmdb.csv')
    
    # Read existing entries
    existing_entries = []
    existing_hostnames = set()
    
    if cmdb_path.exists():
        with open(cmdb_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_entries.append(row)
                existing_hostnames.add(row['hostname'])
    
    # Add new services (skip duplicates)
    new_entries = []
    for service in services:
        if service['hostname'] not in existing_hostnames:
            new_entries.append(service)
    
    # Write updated CSV
    all_entries = existing_entries + new_entries
    
    with open(cmdb_path, 'w', newline='') as f:
        fieldnames = ['hostname', 'ip_address', 'os_type', 'os_version', 
                     'services', 'path', 'user', 'ssh_access_notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_entries)
    
    return len(new_entries), len(all_entries)

def main():
    """Main function"""
    print("Parsing ports.md...")
    services = parse_ports_md()
    print(f"Found {len(services)} services in ports.md")
    
    print("\nUpdating CMDB...")
    new_count, total_count = update_cmdb_csv(services)
    print(f"Added {new_count} new entries to CMDB")
    print(f"Total entries in CMDB: {total_count}")
    
    # Show sample of added services
    if new_count > 0:
        print("\nSample of added services:")
        for service in services[:5]:
            print(f"  - {service['hostname']} ({service['ip_address']})")

if __name__ == '__main__':
    main()