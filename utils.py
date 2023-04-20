def format_name(name):
    name = name.lower().strip().replace(" ", "")
    name = ''.join(e for e in name if e.isalnum())
    return name

async def fetch(url, session):
    async with session.get(url) as response:
        return await response.json()

def add_to_file(file_name, name, data):
    with open(file_name, 'a') as f:
        f.write(name + "," + data + '\n')
        