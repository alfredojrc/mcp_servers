from pykeepass import PyKeePass
import os

# Read password
with open('/run/secrets/keepass_alf_password', 'r') as f:
    password = f.read().strip()

# Open database
kp = PyKeePass('/personal.kdbx', password=password)

print(f'Database opened successfully!')
print(f'Number of entries: {len(kp.entries)}')
print(f'Number of groups: {len(kp.groups)}')

# List groups
print('\nGroups:')
for group in kp.groups:
    if group.name and group.name != 'Root':
        print(f'  - {group.path}')

# Show first few entries (titles only, no passwords)
print('\nFirst 10 entry paths:')
for i, entry in enumerate(kp.entries[:10]):
    if entry.title:
        print(f'  {i+1}. {entry.path}')

# Test retrieving a specific entry
print('\nTesting entry retrieval...')
test_entry = kp.find_entries(path='Root', first=True)
if test_entry:
    print(f'Found entry: {test_entry.title}')
else:
    print('No entry found at Root path')