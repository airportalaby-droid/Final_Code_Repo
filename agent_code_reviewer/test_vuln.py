import os

def vulnerable_function(username, user_input):
    print("This is a vulnerable function")
    

    api_key = "1234567890abcdef"
    password = "super_secret_password"
    

    command = "os.system('rm -rf /')"
    eval(command)


    cursor = get_db_cursor()
    cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
    

    return render_template_string("<h1>Welcome, " + user_input + "</h1>")

def get_db_cursor(): pass
def render_template_string(x): pass

if __name__ == "__main__":
    vulnerable_function("admin", "<script>alert('xss')</script>")
