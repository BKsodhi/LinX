import sys
import json
import difflib
import os
import tempfile
import subprocess
import google.generativeai as genai
api_key = "AIzaSyAXJXgO0rSMEVVhocbuh7zEB90KGM8ZPos"  
USER_FILE = "users.json"
current_user = None

def dialog_input(prompt):
    return subprocess.getoutput(f'dialog --stdout --inputbox "{prompt}" 8 60')

def dialog_msg(msg, title="Message"):
    os.system(f'dialog --title "{title}" --msgbox "{msg}" 10 60')

def dialog_textbox(output):
    with tempfile.NamedTemporaryFile(delete=False, mode="w") as tmp:
        tmp.write(output)
        tmp_path = tmp.name
    os.system(f"dialog --title 'Command Output' --textbox {tmp_path} 20 80")
    os.remove(tmp_path)

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)

def login_or_register():
    global current_user
    users = load_users()
    while True:
        choice = subprocess.getoutput(
            "dialog --clear --stdout --menu 'Welcome to LinX-Assistant' 15 50 4 "
            "1 'Login' "
            "2 'Register' "
            "3 'Exit'"
        )
        if choice == "1":
            email = dialog_input("Enter your email:")
            password = dialog_input("Enter your password:")
            if email in users and users[email]["password"] == password:
                dialog_msg(f"Welcome back, {users[email]['name']}!")
                current_user = users[email]
                break
            else:
                dialog_msg("Invalid credentials. Try again.")
        elif choice == "2":
            name = dialog_input("Enter your name:")
            email = dialog_input("Enter your email:")
            password = dialog_input("Enter password:")
            if email in users:
                dialog_msg("User already exists.")
            else:
                users[email] = {"name": name, "password": password}
                save_users(users)
                dialog_msg("Registration successful. You can now login.")
        elif choice == "3":
            sys.exit(0)
        else:
            dialog_msg("Invalid selection.")

def load_tasks():
    try:
        with open("commands.json", "r") as f:
            return json.load(f)
    except Exception as e:
        dialog_msg(f"Error loading tasks: {e}")
        return {}

def execute_command(cmd):
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        output = e.output
    dialog_textbox(output)

def fetch_gemini_command_suggestions(query):
    try:
        if not api_key:
            return ["Error: GEMINI_API_KEY environment variable not set."]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = f"""I want to learn about this Linux cmd: "{query}".
        Give me 3 best Linux terminal commands (or sequences) for this task.
        Respond with the commands, each on a new line, explanations in 3 lines with no highlights."""
        response = model.generate_content(prompt)
        return [line.strip() for line in response.text.strip().split("\n") if line.strip()]
    except Exception as e:
        return [f"Error from Gemini: {str(e)}"]

def get_main_menu_choice():
    return subprocess.getoutput(
        "dialog --clear --stdout --menu 'LinX-Assistant Menu' 15 50 5 "
        "1 'Search by Task Description' "
        "2 'List Commands by Starting Letter' "
        "3 'Exit'"
    )

def handle_task_description(task_map):
    task_keys = list(task_map.keys())
    user_input = dialog_input("Enter task description:")
    matches = difflib.get_close_matches(user_input, task_keys, n=1, cutoff=0.5)

    if matches:
        suggestion = task_map[matches[0]]
        suggestion = customize_command(suggestion)
        confirm = dialog_input(f"Suggested: {suggestion}\nRun it? (y/n or 'o' for online):")
        if confirm.lower() == 'y':
            dialog_msg(f"Executing:\n{suggestion}")
            execute_command(suggestion)
        elif confirm.lower() == 'o':
            run_gemini_flow(user_input)
        else:
            dialog_msg("Cancelled.")
    else:
        confirm = dialog_input("No match found. Search online? (y/n):")
        if confirm.lower() == "y":
            run_gemini_flow(user_input)
        else:
            dialog_msg("Cancelled.")

def run_gemini_flow(user_input):
    suggestions = fetch_gemini_command_suggestions(user_input)
    if suggestions and not suggestions[0].startswith("Error"):
        numbered = "\n".join([f"{i+1}. {cmd}" for i, cmd in enumerate(suggestions)])
        dialog_textbox(numbered)
        choice = dialog_input("Choose command number to run:")
        if choice.isdigit() and 1 <= int(choice) <= len(suggestions):
            cmd = suggestions[int(choice)-1]
            dialog_msg(f"Executing:\n{cmd}")
            execute_command(cmd)
        else:
            dialog_msg("Cancelled.")
    else:
        dialog_msg("\n".join(suggestions))

def customize_command(command):
    if "<username>" in command:
        user = dialog_input("Enter username:")
        command = command.replace("<username>", user)
    if "<package>" in command:
        pkg = dialog_input("Enter package name:")
        command = command.replace("<package>", pkg)
    if "<dirname>" in command:
        dirname = dialog_input("Enter directory name:")
        command = command.replace("<dirname>", dirname)
    if "<source>" in command and "<destination>" in command:
        src = dialog_input("Enter source path:")
        dest = dialog_input("Enter destination path:")
        command = command.replace("<source>", src).replace("<destination>", dest)
    if "/dev/sdX" in command:
        device = dialog_input("Enter device path (e.g., /dev/sda1):")
        command = command.replace("/dev/sdX", device)
    return command

def handle_starting_letter(task_map):
    commands = list(set(task_map.values()))
    letter = dialog_input("Enter starting letter:")
    suggestions = [cmd for cmd in commands if cmd.startswith(letter)]
    if not suggestions:
        dialog_msg("No command found.")
        return

    numbered = "\n".join([f"{i+1}. {cmd}" for i, cmd in enumerate(suggestions)])
    with tempfile.NamedTemporaryFile(delete=False, mode="w") as tmp:
        tmp.write(numbered)
        tmp_path = tmp.name

    os.system(f"dialog --textbox {tmp_path} 20 60")
    os.remove(tmp_path)

    choice = dialog_input("Choose command number:")
    if choice.isdigit() and 1 <= int(choice) <= len(suggestions):
        chosen_command = customize_command(suggestions[int(choice) - 1])
        dialog_msg(f"Executing:\n{chosen_command}")
        execute_command(chosen_command)
    else:
        dialog_msg("Cancelled.")

def main():
    login_or_register()
    task_map = load_tasks()

    while True:
        choice = get_main_menu_choice()
        if choice == "1":
            handle_task_description(task_map)
        elif choice == "2":
            handle_starting_letter(task_map)
        elif choice == "3" or choice == "":
            dialog_msg("Exiting LinX-Assistant. Goodbye!", "Exit")
            os.system("clear")
            break
        else:
            dialog_msg("Invalid selection.")

if __name__ == "__main__":
    main()
