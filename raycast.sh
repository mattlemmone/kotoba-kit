#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Create Anki Card
# @raycast.mode compact

# Optional parameters:
# @raycast.icon 🇯🇵
# @raycast.description Create an Anki card with TTS for a Japanese phrase
# @raycast.author mattlemmone
# @raycast.authorURL https://github.com/mattlemmone

# @raycast.argument1 { "type": "text", "placeholder": "Japanese phrase", "optional": false }
# @raycast.argument2 { "type": "text", "placeholder": "Custom translation (optional)", "optional": true }

# Get the phrase from the first argument
phrase="$1"
# Get the custom translation from the second argument (optional)
custom_translation="$2"

# Check if phrase is provided
if [ -z "$phrase" ]; then
    echo "Error: Please provide a Japanese phrase"
    exit 1
fi

# Get the directory where the script is located
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory to ensure we're in the right location
cd "$script_dir"

# Set up PATH for Python - try to source shell config or use specific paths
if [ -f "$HOME/.zshrc" ]; then
    source "$HOME/.zshrc" 2>/dev/null || true
fi

# Find Python executable
python_cmd=""
for cmd in python python3 /opt/homebrew/bin/python3 /usr/bin/python3; do
    if command -v "$cmd" >/dev/null 2>&1; then
        python_cmd="$cmd"
        break
    fi
done

if [ -z "$python_cmd" ]; then
    echo "Error: Python not found. Please ensure Python is installed."
    exit 1
fi

# Check if kotobakit.py exists
if [ ! -f "kotobakit.py" ]; then
    echo "Error: kotobakit.py not found in $script_dir"
    exit 1
fi

# Run the kotoba-kit command
echo "Creating Anki card for: $phrase"
if [ -n "$custom_translation" ]; then
    echo "Using custom translation: $custom_translation"
fi
echo "Using Python: $python_cmd"
echo "---"

# Build the command with optional -t flag
if [ -n "$custom_translation" ]; then
    "$python_cmd" kotobakit.py card "$phrase" -t "$custom_translation"
else
    "$python_cmd" kotobakit.py card "$phrase"
fi

# Check if the command was successful
if [ $? -eq 0 ]; then
    echo "---"
    echo "✅ Card created successfully!"
else
    echo "---"
    echo "❌ Error creating card"
    exit 1
fi
