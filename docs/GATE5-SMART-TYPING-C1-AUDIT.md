# Gate 5 Component 1 - Smart Typing Foundation

## Delivered contract

- Literal typing remains bound to an exact, freshly focused target window.
- Characters supported by the active layout use verified virtual-key input.
- Other printable Unicode characters and emoji use Windows UTF-16 `SendInput`.
- The clipboard is never read or changed by either typing path.
- Password fields retain focus/process verification but are never read back.
- Non-printing control characters are rejected before any input is delivered.
- Success still requires fresh focused-control or accessibility-text evidence.

## Manual acceptance

1. Copy a unique token such as `CLIPBOARD-STAYS-42` to the clipboard.
2. Open a new Notepad document.
3. Tell JARVIS: `Type testing 123 Roman Urdu main tayyar hoon in Notepad.`
4. Confirm the sentence appears once, in Notepad, with no missing characters.
5. Open a second blank line and press `Ctrl+V` yourself.
6. Confirm the pasted value is still exactly `CLIPBOARD-STAYS-42`.
7. While Notepad is active, tell JARVIS to type into a different nonexistent
   app. Confirm it reports that the app/target is unavailable and does not type
   into Notepad.

Pass phrase: `Gate 5 Component 1 manual tests passed.`
