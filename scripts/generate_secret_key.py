import secrets

secret_key = secrets.token_hex(32)  # Generates a 64-character hex string
print(f"Generated secret key: {secret_key}")
