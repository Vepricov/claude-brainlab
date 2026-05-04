#!/bin/bash
# Open Claude Code prompt in TextEdit and wait for Cmd+S then Cmd+W.
# Workaround: copies to a .txt temp file (TextEdit handles these cleanly),
# watches for save via fswatch, copies content back, waits for window close.

ORIGINAL="$1"
FSWATCH=/opt/homebrew/bin/fswatch

# Force TextEdit plain text mode
defaults write com.apple.TextEdit RichText 0 2>/dev/null

# Copy to a .txt file TextEdit will handle cleanly
TMP_TXT="$(mktemp /tmp/claude-prompt-XXXXXX).txt"
cp "$ORIGINAL" "$TMP_TXT"

# Open in TextEdit (non-blocking)
open -a TextEdit "$TMP_TXT"
sleep 0.4

# Use osascript to wait until TextEdit closes this specific document
osascript <<APPLESCRIPT
set tmpFile to POSIX file "$TMP_TXT"
tell application "TextEdit"
    activate
end tell
-- Wait for the .txt document to disappear from TextEdit's document list
set docName to do shell script "basename '$TMP_TXT'"
repeat
    delay 0.3
    tell application "TextEdit"
        try
            set openNames to name of every document
        on error
            set openNames to {}
        end try
    end tell
    set found to false
    repeat with n in openNames
        if (n as string) is equal to docName then
            set found to true
            exit repeat
        end if
    end repeat
    if not found then exit repeat
end repeat
APPLESCRIPT

# Copy edited content back to the original file
cp "$TMP_TXT" "$ORIGINAL"
rm -f "$TMP_TXT"
