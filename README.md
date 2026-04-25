# notetaker
Complete hardware and software setup guide for SideNotes, a productivity device used for taking notes.

## Overview
SideNotes is a standalone e-ink notetaker device powered by a Raspberry Pi Zero 2 W and PiSugar S 3.7 V LiPo
battery. In a compact case under 4 inches in length and 1.5 inches thick, it is designed to be lightweight and
portable, allowing you to keep it close by, in your pocket, your purse, or even on a keychain. It is also
designed to be simple, shifting away from the overcomplicated, feature-packed designs of modern smartphones and
computers. Unlike these devices which offer a wide range of versatility, but often leave users scrolling 
endlessly on just 1 or 2 apps for hours, SideNotes has one purpose: improving your productivity. On a device 
that can do anything, it can be hard to stay focused on the important tasks. SideNotes removes these 
distractions and filters out all of the useless information, while keeping the important information organized.
Type notes on a physical keyboard, save them, and read them back all on a paper-like e-ink screen for a 
distraction-free experience.

## Features
- Home screen with Notes app and Files navigation. Easily write and read files directly after boot-up
- Full note editor with cursor movement, backspace, new line, scroll
- File browser to view and edit saved notes organized by date and time
- Partial refresh e-ink rendering for fast keystroke response
- Full refresh every 200 keypresses to clear ghosting
- Notes saved as timestamped .txt files to '/home/pi/notes/'
- Fn+S saves notes at any time without navigating to save menu
- Escape key brings up Save & Quit / Home / Cancel Menu or Power Off / Cancel menu
- Auto-launches on device bootup via systemd
- Screensaver on power off


## Software Setup
See [software/setup.md](software/setup.md) for full OS and library installation instructions
