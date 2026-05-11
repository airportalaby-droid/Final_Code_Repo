# Example vulnerable Python code for testing detectors
user_input = "1 OR 1=1"

# SQL injection via string formatting
query = "SELECT * FROM users WHERE id = %s" % user_input
cursor.execute(query)

# hardcoded secret
API_KEY = "ABCD1234SECRETKEYSHOULDNOTBEHERE"
password = "hunter2"

# safe usage for comparison
cursor.execute("SELECT * FROM users WHERE id = %s", (user_input,))
