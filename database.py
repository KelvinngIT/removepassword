def user_exists(email: str) -> bool:
    """Return True if the email is already registered."""
    # Example with SQLite:
    # conn = get_connection()
    # cur = conn.execute("SELECT 1 FROM users WHERE email = ?", (email,))
    # return cur.fetchone() is not None
    ...

def set_temp_password(email: str, plain_password: str) -> bool:
    """
    Hash the temporary password and update it for the given user.
    Return True on success.
    """
    # hashed = hash_password(plain_password)   # use the same hashing as create_user
    # UPDATE users SET password = ? WHERE email = ?
    ...
