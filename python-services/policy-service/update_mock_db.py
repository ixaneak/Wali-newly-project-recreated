import json

file_path = 'mock_db.json'
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

updated = False
for key in ['User', 'users']:
    if key in data:
        for user in data[key]:
            if user.get('email') == 'admin@wali.com' or user.get('email') == 'admin@wali.ci':
                user['email'] = 'admin@wali.ci'
                updated = True

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)

if updated:
    print('Successfully updated admin email to admin@wali.ci')
else:
    print('Amin user not found or no changes needed.')
