# Time Tracker CLI (tt)

A lightweight, macOS-native command-line time tracking tool for daily work logging.

## Features

- ⏱️ **Simple Time Tracking** - Start/stop timers for customer projects
- 📝 **Task Notes** - Add detailed descriptions to track what you worked on
- 🔄 **15-Minute Rounding** - Automatically rounds up to nearest 15-minute block
- 📊 **Hierarchical Reports** - View time grouped by customer, project, and task
- 📋 **Clipboard Export** - Copy formatted summaries to clipboard (macOS `pbcopy`)
- ⚡ **Shortcuts** - Save recurring tasks and start them instantly with `@shortcut`
- 🔍 **Shell Completion** - TAB completion for shortcuts (zsh/bash) and fzf integration
- 💾 **JSON Storage** - Lightweight persistence in home directory
- 🔀 **Auto Context Switch** - Starting a new task automatically stops the previous one
- 🎯 **Daily Reset** - Designed for single-day workflows

## Requirements

- macOS (uses `pbcopy` for clipboard functionality)
- Python 3.6+ (no external dependencies)

## Installation

### Quick Setup

1. **Clone or download** this repository
2. **Make executable:**
   ```bash
   chmod +x tt.py
   ```
3. **Create an alias** (add to `~/.zshrc`):
   ```bash
   alias tt='python3 /path/to/tt.py'
   ```
4. **Reload shell:**
   ```bash
   source ~/.zshrc
   ```

### Recommended Setup

For easier access, create a symlink:
```bash
sudo ln -s "/Users/$(whoami)/Documents/PY Projects/2025-tt/tt.py" /usr/local/bin/tt
```

## Usage

### Basic Commands

```bash
# Interactive start (select from saved customers/projects)
tt

# Quick start with customer & project IDs
tt start 1 2

# Start with task description
tt start 1 2 "Fixing bug in authentication module"

# Add note to running timer
tt note "Completed code review"

# Stop current timer
tt stop

# View daily report
tt report

# Copy report to clipboard
tt copy

# Add new customers/projects
tt add

# Clear today's data
tt reset

# Show help
tt help
```

### Shortcuts for Recurring Tasks

```bash
# Create a shortcut
tt shortcut add daily "Acme Corp" "Management" "Daily standup meeting"
tt shortcut add review "Acme Corp" "Dev" "Code review session"

# List all shortcuts
tt shortcut list

# Use a shortcut (super fast!)
tt start @daily
tt start -s review

# Start with shortcut and add extra note
tt start @daily "Discussed sprint planning"

# Delete a shortcut
tt shortcut delete daily
```

### Workflow Example

```bash
# Setup shortcuts once (one-time)
$ tt shortcut add daily "Acme Corp" "Management" "Daily standup"
$ tt shortcut add dev "Acme Corp" "Development" "Coding session"
✅ Shortcuts created.

# Morning: Start first task using shortcut
$ tt start @daily
📌 Using shortcut '@daily'
▶️  Started: Acme Corp - Management ('Daily standup')

# Add more notes during work
$ tt note "Reviewed backlog items"
📝 Note added: "Reviewed backlog items"

# Switch to new task (auto-stops previous)
$ tt start @dev "Bug fixing in authentication"
⏹  Stopped: Acme Corp - Management (Billed: 0h 45m)
📌 Using shortcut '@dev'
▶️  Started: Acme Corp - Development ('Coding session, Bug fixing in authentication')

# View daily summary
$ tt report
--- DAILY REPORT (15min blocks, grouped) ---
CUSTOMER        | PROJECT        | TOTAL    | DETAILS
---------------------------------------------------------------------------
Acme Corp       | Development    | 01:00    | 60 min
                                   - Coding session, Bug fixing...        | 60 min
Acme Corp       | Management     | 00:45    | 45 min
                                   - Daily standup, Reviewed backlog...   | 45 min
---------------------------------------------------------------------------
TOTAL: 01:45 (105 min)
```

## Data Storage

- **Config:** `~/.tt_config.json` (customers, projects & shortcuts)
- **Daily Data:** `~/.tt_data.json` (current timer & history)

Both files are simple JSON and can be manually edited if needed.

## Shell Completion

The tool supports TAB completion for shortcuts in zsh and bash. See [SHELL_COMPLETION.md](SHELL_COMPLETION.md) for setup instructions.

## 15-Minute Rounding

All time entries are automatically rounded **up** to the nearest 15-minute block:
- 1-15 minutes → 15 min
- 16-30 minutes → 30 min
- 31-45 minutes → 45 min
- 46-60 minutes → 60 min

The original time is preserved in `raw_seconds` for reference.

## Design Philosophy

This tool follows the "Quick Win" / "Micro-Tool" philosophy:
- Single-file, no dependencies
- Optimized for daily use (not long-term storage)
- Fast and lightweight
- macOS-native integration
- Easy to backup/version (plain JSON)

## License

MIT License - feel free to use and modify as needed.

## Contributing

This is a personal productivity tool, but suggestions and improvements are welcome!

