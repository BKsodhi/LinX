import json
import subprocess
import os
import tempfile

# Function to show input box using dialog
def dialog_input(prompt):
    return subprocess.getoutput(f"dialog --stdout --inputbox \"{prompt}\" 8 60")

# Function to show message
def dialog_msg(msg, title="Message"):
    os.system(f"dialog --title \"{title}\" --msgbox \"{msg}\" 10 60")

# Function to show output in textbox
def dialog_textbox(output):
    with tempfile.NamedTemporaryFile(delete=False, mode="w") as tmp:
        tmp.write(output)
        tmp_path = tmp.name
    os.system(f"dialog --title 'Command Output' --textbox {tmp_path} 20 80")
    os.remove(tmp_path)

# Load commands
def load_commands():
    try:
        with open("commands.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        dialog_msg("Error: commands.json file not found.")
        return {}

# Find best match
def find_command(query, commands_data):
    for category, commands in commands_data.items():
        for cmd in commands:
            if isinstance(cmd, dict) and query.lower() in cmd.get("task", "").lower():
                return cmd.get("command")
            elif isinstance(cmd, str) and query.lower() in cmd.lower():
                return cmd
    return None

# Execute command
def execute_command(command):
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
        return output
    except subprocess.CalledProcessError as e:
        return f"Command failed:\n{e.output}"
    except Exception as e:
        return f"Error: {str(e)}"

# Main logic
def main():
    commands_data = load_commands()
    query = dialog_input("Enter your Linux task or command keyword:")

    matched_command = find_command(query, commands_data)

    if matched_command:
        choice = dialog_input(f"Suggested Command:\n{matched_command}\n\nRun it? (y/n):")
        if choice.lower() == 'y':
            output = execute_command(matched_command)
            dialog_textbox(output)
        else:
            dialog_msg("Cancelled.")
    else:
        choice = dialog_input("No match found. Run your own input as command? (y/n):")
        if choice.lower() == 'y':
            output = execute_command(query)
            dialog_textbox(output)
        else:
            dialog_msg("Cancelled.")

if __name__ == "__main__":
    main()
