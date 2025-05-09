def get_credentials(CREDENTIALS_FILE):
    """Reads the credentials from the file and returns them as a tuple (username, password)."""
    username = None
    password = None

    with open(CREDENTIALS_FILE, 'r') as f:
        for line in f:
            if line.startswith('user:'):
                username = line.split(':')[1].strip()
            elif line.startswith('password:'):
                password = line.split(':')[1].strip()

    return username, password
