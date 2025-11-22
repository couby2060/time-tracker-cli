#!/usr/bin/env python3
import sys
import json
import time
import os
import subprocess
import math
from pathlib import Path
from datetime import datetime

# --- CONFIGURATION ---
# Data for the current day
DATA_FILE = Path.home() / ".tt_data.json"
# Permanent configuration (Customers/Projects)
CONFIG_FILE = Path.home() / ".tt_config.json"

# --- DATA MANAGEMENT ---
def load_json(filepath, default):
    if not filepath.exists():
        return default
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️  Warning: Could not load {filepath.name}. Starting with empty data.")
        return default

def save_json(filepath, data):
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"❌ Error saving data: {e}")

def get_formatted_duration(seconds):
    """Returns (hours, minutes) tuple from seconds."""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return int(h), int(m)

def round_seconds_to_15min(seconds):
    """Rounds up seconds to the nearest 15-minute block."""
    if seconds <= 0: 
        return 0
    minutes = seconds / 60
    # Round up to next 15
    rounded_minutes = math.ceil(minutes / 15) * 15
    return int(rounded_minutes * 60)

def copy_to_clipboard(text):
    """Mac-specific clipboard copy."""
    try:
        process = subprocess.Popen(
            'pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
        process.communicate(text.encode('utf-8'))
    except FileNotFoundError:
        print("⚠️  'pbcopy' not found. Clipboard feature requires macOS.")
    except Exception as e:
        print(f"❌ Error copying to clipboard: {e}")

# --- TIMER LOGIC ---
def stop_current(data, verbose=True):
    if data["current"]:
        c = data["current"]
        start_time = c["start_timestamp"]
        end_time = time.time()
        raw_duration = end_time - start_time
        
        # Avoid negative duration if system clock changed weirdly
        if raw_duration < 0: raw_duration = 0

        # Round up to nearest 15-minute block
        billed_duration = round_seconds_to_15min(raw_duration)
        notes = c.get("notes", [])

        entry = {
            "customer": c["customer"],
            "project": c["project"],
            "duration_seconds": billed_duration,  # Rounded time for billing
            "raw_seconds": raw_duration,          # Keep original time for reference
            "notes": notes,                       # Task descriptions
            "start_str": time.strftime("%H:%M", time.localtime(start_time)),
            "end_str": time.strftime("%H:%M", time.localtime(end_time))
        }
        data["history"].append(entry)
        data["current"] = None
        
        h, m = get_formatted_duration(billed_duration)
        if verbose:
            print(f"⏹  Stopped: {c['customer']} - {c['project']} (Billed: {h}h {m}m)")
        return True
    return False

# --- INTERACTIVE MENU LOGIC ---
def select_from_list(items, prompt_text):
    """Helper to select from a list of dicts or strings."""
    # Allow text input even if list is empty
    if not items:
        print("   (List is empty)")
    else:
        for i, item in enumerate(items, 1):
            label = item.get('name') if isinstance(item, dict) else item
            print(f" [{i}] {label}")
    
    try:
        choice = input(f"{prompt_text} (or type name): ").strip()
        
        # Case 1: User typed a number
        if choice.isdigit() and len(choice) < 10:  # Protect against huge numbers
            idx = int(choice) - 1
            # Only allow number selection if items exist
            if items and 0 <= idx < len(items):
                return items[idx]
            elif not items:
                # List is empty, numbers don't make sense
                print("❌ List is empty, please type a name.")
                return None
            else:
                print("❌ Invalid number.")
                return None
        
        # Case 2: User typed text (works even with empty list)
        if choice: 
            return choice 
        
        # Case 3: Empty input
        print("❌ Invalid input.")
        return None
            
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit()

def get_customer_and_project(args):
    config = load_json(CONFIG_FILE, {"customers": []})
    customers = config["customers"]
    
    customer_name = None
    proj_selection = None
    note = None

    # --- SCENARIO 1: Interactive (No args) ---
    if len(args) == 0:
        print("\n--- SELECT CUSTOMER ---")
        cust_selection = select_from_list(customers, "Select Customer")
        
        if isinstance(cust_selection, dict):
            customer_name = cust_selection['name']
            projects = cust_selection.get('projects', [])
            print(f"\n--- SELECT PROJECT FOR '{customer_name}' ---")
            proj_selection = select_from_list(projects, "Select Project")
        elif isinstance(cust_selection, str):
            customer_name = cust_selection
            proj_selection = input("Enter Project Name: ").strip()
            if not proj_selection:
                print("❌ Project name cannot be empty.")
                sys.exit()
        else:
            print("❌ Selection cancelled.")
            sys.exit()

    # --- SCENARIO 2: Partial Args (e.g., "tt start 1") ---
    elif len(args) == 1:
        # Resolve Customer
        if args[0].isdigit():
            idx = int(args[0]) - 1
            if 0 <= idx < len(customers):
                cust_obj = customers[idx]
                customer_name = cust_obj['name']
                # Now prompt for project
                print(f"\n--- SELECT PROJECT FOR '{customer_name}' ---")
                proj_selection = select_from_list(cust_obj['projects'], "Select Project")
            else:
                print(f"❌ Customer ID {args[0]} not found.")
                sys.exit()
        else:
            # User typed "tt start MyCustomer"
            customer_name = args[0]
            proj_selection = input("Enter Project Name: ").strip()
            if not proj_selection:
                print("❌ Project name cannot be empty.")
                sys.exit()

    # --- SCENARIO 3: Full Args (e.g., "tt start 1 2 [Task Description]") ---
    elif len(args) >= 2:
        raw_cust = args[0]
        raw_proj = args[1]
        
        # Everything after customer and project is treated as a note
        if len(args) > 2:
            note = " ".join(args[2:])
        
        # Resolve Customer
        if raw_cust.isdigit():
            idx = int(raw_cust) - 1
            if 0 <= idx < len(customers):
                cust_obj = customers[idx]
                customer_name = cust_obj['name']
                
                # Resolve Project
                if raw_proj.isdigit():
                    p_idx = int(raw_proj) - 1
                    projects = cust_obj['projects']
                    if 0 <= p_idx < len(projects):
                        proj_selection = projects[p_idx]
                    else:
                        proj_selection = raw_proj  # Fallback to text
                else:
                    proj_selection = raw_proj
            else:
                customer_name = raw_cust  # Fallback
                proj_selection = raw_proj
        else:
            customer_name = raw_cust
            proj_selection = raw_proj

    # Clean up results
    if isinstance(proj_selection, dict): 
        return None, None, None
    return customer_name, proj_selection, note

# --- COMMANDS ---

def cmd_add():
    """Add customers/projects to config."""
    config = load_json(CONFIG_FILE, {"customers": []})
    
    print("\n--- ADD NEW ENTRY ---")
    cust_name = input("Customer Name: ").strip()
    if not cust_name:
        print("❌ Customer name cannot be empty.")
        return
    
    # Check if exists
    customer = next((c for c in config["customers"] if c["name"] == cust_name), None)
    
    if not customer:
        customer = {"name": cust_name, "projects": []}
        config["customers"].append(customer)
        print(f"Created customer '{cust_name}'.")
    
    while True:
        proj = input(f"Add Project for '{cust_name}' (Enter to finish): ").strip()
        if not proj: break
        if proj not in customer["projects"]:
            customer["projects"].append(proj)
            print(f" + Added project '{proj}'")
    
    save_json(CONFIG_FILE, config)
    print("✅ Saved.")

def cmd_shortcut(args):
    """Manage shortcuts for recurring tasks."""
    config = load_json(CONFIG_FILE, {"customers": [], "shortcuts": {}})
    
    # Special flag for shell completion scripts
    if args and args[0] == "--complete":
        shortcuts = config.get("shortcuts", {})
        for name in sorted(shortcuts.keys()):
            print(f"@{name}")
        return
    
    # Special flag for fzf picker
    if args and args[0] == "pick":
        shortcuts = config.get("shortcuts", {})
        if not shortcuts:
            return
        # Print in fzf-friendly format: name\tcustomer\tproject\tnote
        for name, data in sorted(shortcuts.items()):
            note = data.get('note', '')
            print(f"{name}\t{data['customer']}\t{data['project']}\t{note}")
        return
    
    if not args or args[0] == "list":
        # List all shortcuts
        shortcuts = config.get("shortcuts", {})
        if not shortcuts:
            print("No shortcuts defined.")
            print("Create one with: tt shortcut add <name> <customer> <project> [note]")
            return
        
        print("\n--- SHORTCUTS ---")
        for name, data in sorted(shortcuts.items()):
            note_str = f" - {data['note']}" if data.get('note') else ""
            print(f"  @{name:<12} → {data['customer']} / {data['project']}{note_str}")
        print(f"\nTotal: {len(shortcuts)} shortcut(s)")
        print("Usage: tt start @{name} or tt start -s {name}")
        return
    
    action = args[0].lower()
    
    if action == "add":
        if len(args) < 4:
            print("❌ Usage: tt shortcut add <name> <customer> <project> [note]")
            print("   Example: tt shortcut add daily \"Acme Corp\" \"Management\" \"Daily standup\"")
            return
        
        name = args[1].lower()
        customer = args[2]
        project = args[3]
        note = " ".join(args[4:]) if len(args) > 4 else ""
        
        if "shortcuts" not in config:
            config["shortcuts"] = {}
        
        # Check if shortcut already exists
        if name in config["shortcuts"]:
            print(f"⚠️  Shortcut '@{name}' already exists. Overwriting...")
        
        config["shortcuts"][name] = {
            "customer": customer,
            "project": project,
            "note": note
        }
        
        save_json(CONFIG_FILE, config)
        print(f"✅ Shortcut '@{name}' created.")
        print(f"   Use with: tt start @{name}")
    
    elif action == "delete" or action == "remove" or action == "rm":
        if len(args) < 2:
            print("❌ Usage: tt shortcut delete <name>")
            return
        
        name = args[1].lower()
        shortcuts = config.get("shortcuts", {})
        
        if name in shortcuts:
            del shortcuts[name]
            save_json(CONFIG_FILE, config)
            print(f"🗑️  Shortcut '@{name}' deleted.")
        else:
            print(f"❌ Shortcut '@{name}' not found.")
            print("   Run 'tt shortcut list' to see available shortcuts.")
    
    else:
        print("❌ Unknown action. Usage: tt shortcut [list|add|delete]")
        print("   tt shortcut list              - List all shortcuts")
        print("   tt shortcut add <name> ...    - Create a shortcut")
        print("   tt shortcut delete <name>     - Remove a shortcut")

def cmd_start(args):
    data = load_json(DATA_FILE, {"current": None, "history": []})
    
    # Stop current if running
    if data["current"]:
        stop_current(data)

    customer = None
    project = None
    note = None
    
    # Check for shortcut syntax: -s shortcut_name or @shortcut_name
    if args and (args[0] == "-s" or args[0].startswith("@")):
        config = load_json(CONFIG_FILE, {"customers": [], "shortcuts": {}})
        shortcuts = config.get("shortcuts", {})
        
        # Get shortcut name
        if args[0] == "-s":
            if len(args) < 2:
                print("❌ Usage: tt start -s <shortcut_name>")
                print("   Run 'tt shortcut list' to see available shortcuts.")
                return
            shortcut_name = args[1].lower()
            extra_note = " ".join(args[2:]) if len(args) > 2 else ""
        else:  # @shortcut
            shortcut_name = args[0][1:].lower()  # Remove @
            extra_note = " ".join(args[1:]) if len(args) > 1 else ""
        
        if shortcut_name not in shortcuts:
            print(f"❌ Shortcut '@{shortcut_name}' not found.")
            print("   Run 'tt shortcut list' to see available shortcuts.")
            return
        
        # Load from shortcut
        shortcut = shortcuts[shortcut_name]
        customer = shortcut["customer"]
        project = shortcut["project"]
        note = shortcut.get("note", "")
        
        # Append extra note if provided
        if extra_note:
            note = f"{note}, {extra_note}" if note else extra_note
        
        print(f"📌 Using shortcut '@{shortcut_name}'")
    else:
        # Normal flow
        customer, project, note = get_customer_and_project(args)
    
    if not customer or not project:
        print("❌ Cancelled or Invalid Input.")
        return

    # Prepare notes list
    notes_list = []
    if note:
        notes_list.append(note)

    # Start
    data["current"] = {
        "customer": customer,
        "project": project,
        "start_timestamp": time.time(),
        "notes": notes_list
    }
    save_json(DATA_FILE, data)
    
    msg = f"▶️  Started: {customer} - {project}"
    if note:
        msg += f" ('{note}')"
    print(msg)

def cmd_note(args):
    """Add a note to the currently running timer."""
    data = load_json(DATA_FILE, {"current": None, "history": []})
    
    if not data["current"]:
        print("❌ No timer running.")
        return
    
    if not args:
        print("❌ Note cannot be empty.")
        return
    
    new_note = " ".join(args)
    if "notes" not in data["current"]:
        data["current"]["notes"] = []
    
    data["current"]["notes"].append(new_note)
    save_json(DATA_FILE, data)
    print(f"📝 Note added: \"{new_note}\"")

def cmd_stop():
    data = load_json(DATA_FILE, {"current": None, "history": []})
    if stop_current(data):
        save_json(DATA_FILE, data)
    else:
        print("No timer running.")

def cmd_report(copy_mode=False):
    data = load_json(DATA_FILE, {"current": None, "history": []})
    
    # Structure: 
    # summary[(Cust, Proj)] = { 
    #     "total_seconds": 0, 
    #     "tasks": {"TaskName": seconds, "TaskName2": seconds} 
    # }
    summary = {} 
    
    def process_entry(cust, proj, seconds, notes_list):
        """Helper to aggregate entry into summary structure."""
        key = (cust, proj)
        if key not in summary:
            summary[key] = {"total_seconds": 0, "tasks": {}}
        
        summary[key]["total_seconds"] += seconds
        
        # Create a Task Name from notes, or use default
        if notes_list:
            task_name = ", ".join(notes_list)
        else:
            task_name = "No Description"
            
        # Add to specific task bucket
        current_task_time = summary[key]["tasks"].get(task_name, 0)
        summary[key]["tasks"][task_name] = current_task_time + seconds

    # Process History
    for entry in data["history"]:
        process_entry(
            entry["customer"], 
            entry["project"], 
            entry["duration_seconds"], 
            entry.get("notes", [])
        )
    
    # Process Current Running Timer
    if data["current"]:
        c = data["current"]
        raw = time.time() - c["start_timestamp"]
        billed = round_seconds_to_15min(raw)
        process_entry(
            c["customer"], 
            c["project"], 
            billed, 
            c.get("notes", [])
        )

    # --- SORTING ---
    # Sort by Customer Name (index 0 of key), then Project Name (index 1)
    sorted_items = sorted(summary.items(), key=lambda x: (x[0][0].lower(), x[0][1].lower()))

    # --- OUTPUT ---
    print("\n--- DAILY REPORT (15min blocks, grouped) ---")
    print(f"{'CUSTOMER':<15} | {'PROJECT':<15} | {'TOTAL':<8} | {'DETAILS'}")
    print("-" * 75)
    
    total_day_seconds = 0
    clipboard_text = ""
    
    for (cust, proj), info in sorted_items:
        total_seconds = info["total_seconds"]
        total_day_seconds += total_seconds
        
        th, tm = get_formatted_duration(total_seconds)
        total_min = int(total_seconds / 60)
        
        # Main line (Customer | Project | Total Time)
        print(f"{cust:<15} | {proj:<15} | {th:02d}:{tm:02d}    | {total_min} min")
        
        # Details (Tasks)
        task_items = []
        for task_name, task_seconds in info["tasks"].items():
            t_min = int(task_seconds / 60)
            t_h, t_m = get_formatted_duration(task_seconds)
            print(f"{'':<35}  - {task_name:<25} | {t_min} min")
            
            # Collect for clipboard
            if task_name != "No Description":
                task_items.append(f"{task_name} ({t_min}m)")
        
        # Build clipboard string
        if task_items:
            details = ", ".join(task_items)
            clipboard_text += f"{cust} - {proj}: {total_min} min [{details}]\n"
        else:
            clipboard_text += f"{cust} - {proj}: {total_min} min\n"

    print("-" * 75)
    day_h, day_m = get_formatted_duration(total_day_seconds)
    print(f"TOTAL: {day_h:02d}:{day_m:02d} ({int(total_day_seconds/60)} min)")
    
    if data["current"]:
        print("\n(⚠️  Includes currently running timer)")

    if copy_mode:
        copy_to_clipboard(clipboard_text)
        print("\n📋 Detailed summary copied to clipboard!")

def cmd_reset():
    print("⚠️  WARNING: This will delete all time entries for today.")
    choice = input("Are you sure? (y/N): ").lower()
    if choice == 'y':
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        print("🗑️  Daily data cleared.")
    else:
        print("Cancelled.")

def cmd_help():
    print("\n--- TIME TRACKER HELP ---")
    print("Note: All times are rounded up to the nearest 15 minutes per session.")
    print("-" * 70)
    print("BASIC COMMANDS:")
    print("  tt start                    -> Interactive menu")
    print("  tt start 1 2 [Task]         -> Quick start with optional task description")
    print("  tt start @<shortcut>        -> Start using a saved shortcut")
    print("  tt start -s <shortcut>      -> Alternative shortcut syntax")
    print("  tt note \"Text\"              -> Add note to current running task")
    print("  tt stop                     -> Stop timer")
    print("  tt report                   -> View detailed breakdown")
    print("  tt copy                     -> Copy detailed breakdown to clipboard")
    print()
    print("SHORTCUTS (for recurring tasks):")
    print("  tt shortcut list            -> List all saved shortcuts")
    print("  tt shortcut add <name> ...  -> Create a new shortcut")
    print("  tt shortcut delete <name>   -> Remove a shortcut")
    print()
    print("CONFIGURATION:")
    print("  tt add                      -> Add customers/projects to config")
    print("  tt reset                    -> Clear today's data")
    print()
    print("Example workflow:")
    print("  tt shortcut add daily \"Acme\" \"Mgmt\" \"Daily standup\"")
    print("  tt start @daily")
    print("  tt note \"Discussed sprint goals\"")
    print("  tt stop")

def main():
    if len(sys.argv) < 2:
        cmd_start([]) # Default to interactive start
        return

    cmd = sys.argv[1].lower()
    
    if cmd == "start":
        cmd_start(sys.argv[2:])
    elif cmd == "shortcut" or cmd == "shortcuts":
        cmd_shortcut(sys.argv[2:])
    elif cmd == "note":
        cmd_note(sys.argv[2:])
    elif cmd == "add":
        cmd_add()
    elif cmd == "stop" or cmd == "pause":
        cmd_stop()
    elif cmd == "report" or cmd == "status":
        cmd_report(copy_mode=False)
    elif cmd == "copy":
        cmd_report(copy_mode=True)
    elif cmd == "reset":
        cmd_reset()
    elif cmd == "help" or cmd == "-h" or cmd == "--help":
        cmd_help()
    else:
        # Shortcut: "tt 1 2" -> "tt start 1 2"
        cmd_start(sys.argv[1:])

if __name__ == "__main__":
    main()