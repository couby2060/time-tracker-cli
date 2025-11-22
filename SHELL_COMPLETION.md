# Shell Completion Setup for Time Tracker

This guide explains how to set up shell autocomplete for the Time Tracker CLI tool, enabling TAB completion for shortcuts and commands.

## Table of Contents
- [Zsh Completion (Recommended)](#zsh-completion-recommended)
- [FZF Integration (Alternative)](#fzf-integration-alternative)
- [Bash Completion](#bash-completion)

---

## Zsh Completion (Recommended)

### Installation

**1. Create the completion file:**

Create a file at `~/.zsh/completions/_tt` with the following content:

```zsh
#compdef tt

_tt() {
    local -a commands shortcuts
    
    commands=(
        'start:Start a new timer'
        'stop:Stop the current timer'
        'note:Add a note to running timer'
        'report:View daily summary'
        'copy:Copy report to clipboard'
        'add:Add customer/project'
        'shortcut:Manage shortcuts'
        'reset:Clear daily data'
        'help:Show help'
    )
    
    # Read shortcuts dynamically from config
    local config_file="$HOME/.tt_config.json"
    if [[ -f "$config_file" ]]; then
        # Use the built-in --complete flag
        local shortcut_lines
        shortcut_lines=(${(f)"$(tt shortcut --complete 2>/dev/null)"})
        
        # Build descriptions from full config
        for shortcut in $shortcut_lines; do
            local name="${shortcut#@}"
            local desc=$(python3 -c "
import json
try:
    with open('$config_file') as f:
        data = json.load(f)
        s = data.get('shortcuts', {}).get('$name', {})
        print(f\"{s.get('customer', '')} - {s.get('project', '')}\")
except: pass
" 2>/dev/null)
            shortcuts+=("$shortcut:$desc")
        done
    fi
    
    _arguments -C \
        '1: :->command' \
        '*:: :->args'
    
    case $state in
        command)
            _describe 'command' commands
            ;;
        args)
            case $words[1] in
                start)
                    # Offer shortcuts when typing @ or after -s
                    if [[ $words[CURRENT-1] == "-s" ]] || [[ $PREFIX == @* ]]; then
                        _describe 'shortcut' shortcuts
                    fi
                    ;;
                shortcut|shortcuts)
                    if [[ $CURRENT -eq 2 ]]; then
                        local -a shortcut_commands
                        shortcut_commands=(
                            'list:List all shortcuts'
                            'add:Create new shortcut'
                            'delete:Remove shortcut'
                        )
                        _describe 'shortcut command' shortcut_commands
                    fi
                    ;;
            esac
            ;;
    esac
}

_tt "$@"
```

**2. Update your `~/.zshrc`:**

Add these lines to your `~/.zshrc` file:

```bash
# Enable completion system
fpath=(~/.zsh/completions $fpath)
autoload -Uz compinit
compinit
```

**3. Reload your shell:**

```bash
source ~/.zshrc
# or simply open a new terminal
```

### Usage

Now you can use TAB completion:

```bash
# Complete commands
tt <TAB>
# Shows: start, stop, note, report, copy, add, shortcut, reset, help

# Complete shortcuts after @
tt start @<TAB>
# Shows: @daily, @review, @meeting (with descriptions)

# Complete shortcuts after -s
tt start -s <TAB>
# Shows: @daily, @review, @meeting

# Complete shortcut subcommands
tt shortcut <TAB>
# Shows: list, add, delete
```

---

## FZF Integration (Alternative)

If you have [fzf](https://github.com/junegunn/fzf) installed, you can use an interactive picker instead.

### Installation

**1. Add this function to your `~/.zshrc`:**

```bash
# Interactive shortcut picker
tts() {
    local shortcut
    shortcut=$(tt shortcut pick | fzf \
        --height 40% \
        --border \
        --prompt "Select shortcut: " \
        --header "TAB to select, ENTER to confirm" \
        --with-nth 1,2,3 \
        --delimiter '\t' \
        --preview 'echo "Customer: {2}\nProject: {3}\nNote: {4}"' \
        | cut -f1)
    
    if [[ -n "$shortcut" ]]; then
        tt start "@$shortcut"
    fi
}
```

**2. Reload shell:**

```bash
source ~/.zshrc
```

### Usage

```bash
# Type 'tts' and get interactive fuzzy-searchable picker
tts

# You'll see something like:
# ┌─ Select shortcut: ────────────────────────┐
# │ daily     Acme Corp    Management          │
# │ review    Acme Corp    Development         │
# │ meeting   Client X     Consulting          │
# └────────────────────────────────────────────┘
```

Use arrow keys or type to fuzzy search, then press ENTER to start.

---

## Bash Completion

For bash users (less feature-rich than zsh):

### Installation

**1. Create `/usr/local/etc/bash_completion.d/tt`:**

```bash
_tt_completion() {
    local cur prev commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    commands="start stop note report copy add shortcut reset help"
    
    case "${prev}" in
        tt)
            COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
            return 0
            ;;
        start)
            if [[ ${cur} == @* ]] || [[ ${prev} == "-s" ]]; then
                local shortcuts=$(tt shortcut --complete 2>/dev/null)
                COMPREPLY=( $(compgen -W "${shortcuts}" -- ${cur}) )
            fi
            return 0
            ;;
        shortcut|shortcuts)
            COMPREPLY=( $(compgen -W "list add delete" -- ${cur}) )
            return 0
            ;;
    esac
}

complete -F _tt_completion tt
```

**2. Add to `~/.bashrc` or `~/.bash_profile`:**

```bash
# Load tt completions
if [ -f /usr/local/etc/bash_completion.d/tt ]; then
    . /usr/local/etc/bash_completion.d/tt
fi
```

**3. Reload:**

```bash
source ~/.bashrc
```

---

## Troubleshooting

### Completions not working

1. **Verify completion file location:**
   ```bash
   ls -la ~/.zsh/completions/_tt
   ```

2. **Check fpath:**
   ```bash
   echo $fpath | grep completions
   ```

3. **Rebuild completion cache:**
   ```bash
   rm -f ~/.zcompdump
   compinit
   ```

4. **Test tt command directly:**
   ```bash
   tt shortcut --complete
   # Should output: @daily, @review, etc.
   ```

### FZF not found

Install fzf via Homebrew:
```bash
brew install fzf
```

### Permissions issues

Make sure the completion file is readable:
```bash
chmod 644 ~/.zsh/completions/_tt
```

---

## Advanced: Custom Completion Behavior

### Modify shortcut display format

Edit the `_tt` function in `~/.zsh/completions/_tt` to customize how shortcuts are displayed:

```zsh
# Show only shortcut names (simpler)
shortcuts=(${(f)"$(tt shortcut --complete 2>/dev/null)"})

# Show with full details (current default)
for shortcut in $shortcut_lines; do
    # ... (existing code)
done
```

### Add color to FZF picker

Update the `tts` function with fzf color options:

```bash
tts() {
    local shortcut
    shortcut=$(tt shortcut pick | fzf \
        --height 40% \
        --border \
        --color 'border:#a89984,header:#fe8019' \
        --prompt "⚡ Select shortcut: " \
        # ... rest of options
    )
}
```

---

## Testing

After setup, test your completion:

```bash
# Test command completion
tt <TAB><TAB>

# Test shortcut completion
tt start @<TAB><TAB>

# Test fzf picker (if installed)
tts
```

---

## LLM Setup Instructions

**To set this up on a new computer, tell your LLM:**

> "I have a Time Tracker CLI tool called `tt` installed. I need to set up shell autocomplete for shortcuts. The tool has a `tt shortcut --complete` command that outputs available shortcuts. Please:
> 
> 1. Create a zsh completion file at `~/.zsh/completions/_tt` 
> 2. Update my `~/.zshrc` to load completions from that directory
> 3. Make shortcuts autocomplete after `tt start @` or `tt start -s`
> 
> The completion file should dynamically read shortcuts using `tt shortcut --complete` and offer them as TAB completion options. Follow the instructions in my SHELL_COMPLETION.md file."

Then paste the contents of this file to the LLM.

---

## See Also

- [Main README](README.md) - Full documentation
- [Zsh Completion System](http://zsh.sourceforge.net/Doc/Release/Completion-System.html)
- [FZF Documentation](https://github.com/junegunn/fzf)

