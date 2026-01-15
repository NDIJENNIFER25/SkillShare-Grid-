from auth_utils import hash_password

def setup_credentials():
    """Read credentials.txt and hash all passwords"""
    print("🔐 Setting up secure credentials...")

    credentials = []

    # Read the file
    with open('credentials.txt', 'r') as file:
        for line in file:
            parts = line.strip().split(',')
            if len(parts) == 3:
                username, email, password = parts
                # Hash the password if not already hashed
                if not password.startswith('$2b$'):
                    hashed_password = hash_password(password)
                    credentials.append(f"{username},{email},{hashed_password}")
                    print(f"✅ Hashed password for: {username}")
                else:
                    credentials.append(line.strip())
                    print(f"⏭️  Already hashed: {username}")

    # Write back to file
    with open('credentials.txt', 'w') as file:
        for cred in credentials:
            file.write(cred + '\n')

    print("\n✅ Credentials setup complete!")

if __name__ == '__main__':

    setup_credentials()
