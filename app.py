# notetaker - app.py
# note taking application for Raspberry Pi Zero 2 W
# Written in Python 3
# Hardware:
#   - Waveshare 2.13" e-Paper HAT V4 (black/white, SPI)
#   - M5Stack CardKB v1.1 (I2C, address 0x5F)
#   - Raspberry Pi Zero 2 W
# Controls:
#   Arrow keys: navigate menus and move cursor in editor
#   Enter: select / new line
#   Backspace: delete character
#   Fn+S (0x9b): save current note
#   Escape: open exit menu (Save & Quit / Home / Cancel) (Power Off / Cancel)
#   Notes are saved as timestamped .txt files in ~/notes/

import time # clock + timekeeping
import smbus2 # i2c communication with cardKB
import textwrap # word wrapping for e-ink display
import os
from PIL import Image, ImageDraw, ImageFont #drawing library for e-ink
from waveshare_epd import epd2in13_V4 # waveshare display driver
from datetime import datetime

# display dimensions (pixels)
W, H = 122, 250 

# font path (monospace)
FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'

# directory for saving notes
NOTES_DIR = '/home/pi/notes'

# key byte values from cardKB, determined by running key detection scripts and pressing each key
KEY_BACKSPACE = 0x08
KEY_ENTER     = 0x0d
KEY_ESC       = 0x1b
# arrows
KEY_UP        = 0xb5
KEY_DOWN      = 0xb6
KEY_LEFT      = 0xb4
KEY_RIGHT     = 0xb7
# fn+save shortcut
FN_SAVE       = 0x9b

# application states
HOME    = 'home' 
FILES   = 'files'
EDIT    = 'edit' 
CONFIRM = 'confirm'

# inititalize display
epd = epd2in13_V4.EPD()
epd.init()
epd.Clear(0xFF) # 0xFF = white

# load fonts at three sizes
font    = ImageFont.truetype(FONT_PATH, 11) # body text
font_sm = ImageFont.truetype(FONT_PATH, 9) # status bar and small labels
font_lg = ImageFont.truetype(FONT_PATH, 13) # large headings

# create image buffer
# all drawing happens on this image in memory, which is then sent to display
img  = Image.new('1', (H, W), 255) # 1 bit black/white, 255 = white background
draw = ImageDraw.Draw(img)

# initialize i2c bus for cardkb
bus = smbus2.SMBus(1) # i2c bus 1 on pins 3 + 5 GPIO header

# display + refresh functions 
def full_refresh():

    epd.init()
    epd.Clear(0xFF)
    epd.display(epd.getbuffer(img))
    epd.displayPartBaseImage(epd.getbuffer(img))

def partial_refresh():

    epd.displayPartial(epd.getbuffer(img))

# drawing utility functions
def clear():

    draw.rectangle([(0,0),(H-1,W-1)], fill=255)

def status_bar(left='', right=''):
   
    draw.rectangle([(0,0),(H-1,12)], fill=0)   # black background
    draw.text((2,2), left, font=font_sm, fill=255)   # white text left
    if right:
        draw.text((H-len(right)*6-2,2), right, font=font_sm, fill=255)   # white text right

# Note file management

def get_notes():

    os.makedirs(NOTES_DIR, exist_ok=True)
    files = [f for f in os.listdir(NOTES_DIR) if f.endswith('.txt')]
    files.sort(reverse=True)
    return files

def load_note(fname):

    with open(os.path.join(NOTES_DIR, fname), 'r') as f:
        return f.read()

def save_note(fname, text):

    os.makedirs(NOTES_DIR, exist_ok=True)
    with open(os.path.join(NOTES_DIR, fname), 'w') as f:
        f.write(text)

# Keyboard Input

def read_key():

    try:
        val = bus.read_byte(0x5F)   # 0x5F is the cardkb i2c address
        return val if val != 0 else None
    except:
        return None

# Home screen

def draw_home(selected=0):
    #draw home screen with two navigation icons for writing notes and reading files
    #selected index of currently highlighted icon (0 = write, 1 = files)
    clear()
    status_bar('notetaker', datetime.now().strftime('%H:%M'))

    icons = ['Write', 'Files']
    box_w = 80    # width of each icon box in pixels
    box_h = 50    # height of each icon box
    gap   = 20    # gap between boxes
    total = len(icons) * box_w + (len(icons)-1) * gap
    start_x = (H - total) // 2   # center boxes horizontally
    y = (W - box_h) // 2          # center boxes vertically

    for i, label in enumerate(icons):
        x = start_x + i * (box_w + gap)
        if i == selected:
            # selected icon: black background, white text
            draw.rectangle([(x,y),(x+box_w,y+box_h)], fill=0)
            draw.text((x+box_w//2-len(label)*3, y+box_h//2-6), label, font=font, fill=255)
        else:
            # unselected icon: white background, black outline, black text
            draw.rectangle([(x,y),(x+box_w,y+box_h)], outline=0, fill=255)
            draw.text((x+box_w//2-len(label)*3, y+box_h//2-6), label, font=font, fill=0)

    # navigation hint at bottom
    draw.text((2, W-12), 'arrows:navigate  enter:select', font=font_sm, fill=0)

def home_screen():
    #main home screen loop
    #left/right arrows move between icons
    #enter selects highlighted icon
    #escape shows power off menu
    selected = 0
    draw_home(selected)
    full_refresh()

    while True:
        val = read_key()
        if val is None:
            time.sleep(0.01)
            continue

        if val in (KEY_LEFT, KEY_RIGHT):
            # toggle between write (0) and files (1)
            selected = 1 - selected
            draw_home(selected)
            partial_refresh()

        elif val == KEY_ENTER:
            if selected == 0:
                edit_screen(new=True)       # open blank note editor
            else:
                files_screen()              # open file browser
            draw_home(selected)
            full_refresh()

        elif val == KEY_ESC:
            # show power off menu
            clear()
            status_bar('power off?', '')
            draw.rectangle([(10,25),(H-10,55)], fill=0)
            draw.text((20,32), 'Power Off', font=font, fill=255)
            draw.rectangle([(10,60),(H-10,90)], outline=0, fill=255)
            draw.text((20,67), 'Cancel', font=font, fill=0)
            full_refresh()

            confirm_sel = 0
            while True:
                v = read_key()
                if v is None:
                    time.sleep(0.01)
                    continue
                if v in (KEY_UP, KEY_DOWN):
                    confirm_sel = 1 - confirm_sel
                    clear()
                    status_bar('power off?', '')
                    if confirm_sel == 0:
                        draw.rectangle([(10,25),(H-10,55)], fill=0)
                        draw.text((20,32), 'Power Off', font=font, fill=255)
                        draw.rectangle([(10,60),(H-10,90)], outline=0, fill=255)
                        draw.text((20,67), 'Cancel', font=font, fill=0)
                    else:
                        draw.rectangle([(10,25),(H-10,55)], outline=0, fill=255)
                        draw.text((20,32), 'Power Off', font=font, fill=0)
                        draw.rectangle([(10,60),(H-10,90)], fill=0)
                        draw.text((20,67), 'Cancel', font=font, fill=255)
                    partial_refresh()
                elif v == KEY_ENTER:
                    if confirm_sel == 0:
                        # show goodbye screensaver and exit
                        clear()
                        font_bye = ImageFont.truetype(FONT_PATH, 20)
                        draw.text((55, 45), 'goodbye', font=font_bye, fill=0)
                        draw.text((50, 75), 'safe to power off', font=font_sm, fill=0)
                        full_refresh()
                        epd.sleep()
                        import sys
                        sys.exit(0)
                    else:
                        break   # cancel, return to home screen
                elif v == KEY_ESC:
                    break
                time.sleep(0.01)

            draw_home(selected)
            full_refresh()

        time.sleep(0.01)

# files

def draw_files(notes, selected, scroll):
    # draw file browser showing a scrollable list of saved notes
    # notes: list of filenames from get_notes()
    # selected: index of currently highlighted note
    # scroll: index of first visible note (for scrolling)
    clear()
    status_bar('files', datetime.now().strftime('%H:%M'))

    if not notes:
        draw.text((2,20), '(no notes yet)', font=font, fill=0)
        draw.text((2,36), 'Press Esc to go back', font=font_sm, fill=0)
        return

    line_h    = 14                          # pixels per list item
    max_lines = (W - 16) // line_h         # how many items fit on screen

    for i in range(max_lines):
        idx = scroll + i
        if idx >= len(notes):
            break
        y    = 16 + i * line_h
        name = notes[idx].replace('.txt','')   # strip file extension for display
        if len(name) > 28:
            name = name[:25] + '...'           # shorten long filenames
        if idx == selected:
            draw.rectangle([(0,y-1),(H-1,y+line_h-2)], fill=0)
            draw.text((2,y), name, font=font_sm, fill=255)
        else:
            draw.text((2,y), name, font=font_sm, fill=0)

    # scroll indicators
    if scroll > 0:
        draw.text((H-8, 16), '^', font=font_sm, fill=0)
    if scroll + max_lines < len(notes):
        draw.text((H-8, W-12), 'v', font=font_sm, fill=0)

def files_screen():
    # file browser screen loop
    # up/down arrows scroll through notes
    # enter opens selected note to edit
    # escape returns to home screen
    notes    = get_notes()
    selected = 0
    scroll   = 0
    line_h    = 14
    max_lines = (W - 16) // line_h

    draw_files(notes, selected, scroll)
    full_refresh()

    while True:
        val = read_key()
        if val is None:
            time.sleep(0.01)
            continue

        if val == KEY_UP and selected > 0:
            selected -= 1
            if selected < scroll:
                scroll -= 1
            draw_files(notes, selected, scroll)
            partial_refresh()

        elif val == KEY_DOWN and notes and selected < len(notes)-1:
            selected += 1
            if selected >= scroll + max_lines:
                scroll += 1
            draw_files(notes, selected, scroll)
            partial_refresh()

        elif val == KEY_ENTER and notes:
            # load the selected note and open it in the editor
            text = load_note(notes[selected])
            edit_screen(new=False, fname=notes[selected], initial_text=text)
            notes = get_notes()   # refresh list in case note was renamed/deleted
            draw_files(notes, selected, scroll)
            full_refresh()

        elif val == KEY_ESC:
            return   # back to home screen

        time.sleep(0.01)

# notetaker / text editor

def get_cursor_pos(text, cursor):
    # given full note text and cursor position, return visual line number, column and list of wrapped lines
    # this is needed because the display wraps long lines 
    # also noted that the cursors character index in the raw text doesn't directly correspond to a row/column position
    lines = []
    for para in text.split('\n'):
        wrapped = textwrap.wrap(para, width=34) or ['']
        lines.extend(wrapped)
    if not lines:
        lines = ['']

    pos = 0
    for li, line in enumerate(lines):
        end = pos + len(line)
        if pos <= cursor <= end:
            return li, cursor - pos, lines
        pos = end + 1
    return len(lines)-1, len(lines[-1]), lines

def draw_edit(text, cursor, scroll, fname=None, dirty=False):
    # draw note editor with current text and cursor position
    # text: current note content as a string
    # cursor: character index of the cursor in the text
    # scroll: index of first visible line for scrolling
    # fname: filename if editing an existing note, none if new
    # dirty: true if there are unsaved changes ( shows * in status bar )

    # returns updated scroll value
    clear()

    # status bar label reflects save state
    if fname and dirty:
        mode = 'edit*'
    elif fname:
        mode = 'edit'
    elif dirty:
        mode = 'new*'
    else:
        mode = 'new'
    status_bar(mode, datetime.now().strftime('%H:%M'))

    line_h    = 14
    max_lines = (W - 16) // line_h

    cursor_line, cursor_col, lines = get_cursor_pos(text, cursor)

    # auto-scroll to keep cursor visible
    if cursor_line < scroll:
        scroll = cursor_line
    elif cursor_line >= scroll + max_lines:
        scroll = cursor_line - max_lines + 1

    # draw each visible line
    for i in range(max_lines):
        idx = scroll + i
        if idx >= len(lines):
            break
        y    = 16 + i * line_h
        line = lines[idx]
        if idx == cursor_line:
            # draw cursor as a vertical bar between characters
            pre  = line[:cursor_col]
            post = line[cursor_col:]
            x = 2
            if pre:
                draw.text((x,y), pre, font=font, fill=0)
                x += len(pre) * 7
            draw.line([(x,y),(x,y+11)], fill=0, width=1)   # Cursor bar
            x += 2
            if post:
                draw.text((x,y), post, font=font, fill=0)
        else:
            draw.text((2,y), line, font=font, fill=0)

    # scroll indicators
    if scroll > 0:
        draw.text((H-8,16), '^', font=font_sm, fill=0)
    if scroll + max_lines < len(lines):
        draw.text((H-8,W-12), 'v', font=font_sm, fill=0)

    return scroll

def draw_confirm():
# draw exit menu
    clear()
    status_bar('exit?', '')
    draw.rectangle([(10,20),(H-10,W-10)], fill=255, outline=0)
    draw.text((20,30), 'Save & Quit', font=font, fill=0)
    draw.text((20,50), 'Home', font=font, fill=0)
    draw.text((20,70), 'Cancel', font=font, fill=0)

def edit_screen(new=True, fname=None, initial_text=''):

    # Note editor screen loop
    # new: true if creating a new note, false if editing existing
    # fname: filename of existing note being edited (none if new)
    # initial_text: pre loaded text content when editing an existing note

    # Key behavior
    # Printable Characters: inserted at cursor position
    # Backspace: deletes character before cursor
    # Enter: inserts newline at cursor
    # Arrow Keys: move cursor through text
    # Fn+S: save note immediately
    # Escape: show exit menu

    text   = initial_text
    cursor = len(text)   # start cursor at end of text
    scroll = 0
    dirty  = False       # track unsaved changes
    count  = 0           # keypress counter for triggering full refresh

    scroll = draw_edit(text, cursor, scroll, fname, dirty)
    full_refresh()

    while True:
        val = read_key()
        if val is None:
            time.sleep(0.01)
            continue

        # escape: show exit dialog
        if val == KEY_ESC:
            draw_confirm()
            # highlight first option by default
            draw.rectangle([(10,27),(H-10,42)], fill=0)
            draw.text((20,30), 'Save & Quit', font=font, fill=255)
            full_refresh()
            confirm_sel = 0

            while True:
                v = read_key()
                if v is None:
                    time.sleep(0.01)
                    continue
                if v == KEY_UP and confirm_sel > 0:
                    confirm_sel -= 1
                elif v == KEY_DOWN and confirm_sel < 2:
                    confirm_sel += 1
                elif v == KEY_ENTER:
                    if confirm_sel == 0:   # save + quit
                        if not fname:
                            fname = datetime.now().strftime('%Y%m%d_%H%M%S') + '.txt'
                        save_note(fname, text)
                        return
                    elif confirm_sel == 1:  # home (save silently if dirty)
                        if dirty:
                            if not fname:
                                fname = datetime.now().strftime('%Y%m%d_%H%M%S') + '.txt'
                            save_note(fname, text)
                        return
                    elif confirm_sel == 2:  # cancel: back to editing
                        break
                elif v == KEY_ESC:
                    break

                # redraw dialog with updated selection highlighted
                draw_confirm()
                options = ['Save & Quit', 'Home', 'Cancel']
                for i, opt in enumerate(options):
                    y = 30 + i * 20
                    if i == confirm_sel:
                        draw.rectangle([(10,y-3),(H-10,y+13)], fill=0)
                        draw.text((20,y), opt, font=font, fill=255)
                    else:
                        draw.text((20,y), opt, font=font, fill=0)
                partial_refresh()
                time.sleep(0.01)

            # resume editing after cancel
            scroll = draw_edit(text, cursor, scroll, fname, dirty)
            full_refresh()
            continue

        # Arrow keys: cursor navigation 
        cursor_line, cursor_col, lines = get_cursor_pos(text, cursor)

        if val == KEY_UP:
            if cursor_line > 0:
                target_line = cursor_line - 1
                pos = sum(len(l)+1 for l in lines[:target_line])
                cursor = min(pos + cursor_col, pos + len(lines[target_line]))

        elif val == KEY_DOWN:
            if cursor_line < len(lines)-1:
                target_line = cursor_line + 1
                pos = sum(len(l)+1 for l in lines[:target_line])
                cursor = min(pos + cursor_col, pos + len(lines[target_line]))

        elif val == KEY_LEFT:
            if cursor > 0:
                cursor -= 1

        elif val == KEY_RIGHT:
            if cursor < len(text):
                cursor += 1

        # Fn+S: save
        elif val == FN_SAVE:
            if not fname:
                fname = datetime.now().strftime('%Y%m%d_%H%M%S') + '.txt'
            save_note(fname, text)
            dirty = False
            status_bar('saved!', datetime.now().strftime('%H:%M'))
            partial_refresh()
            time.sleep(0.8)   # brief confirmation pause

        # Backspace
        elif val == KEY_BACKSPACE and cursor > 0:
            text   = text[:cursor-1] + text[cursor:]
            cursor -= 1
            dirty  = True
            count  += 1

        # Enter: new line
        elif val == KEY_ENTER:
            text   = text[:cursor] + '\n' + text[cursor:]
            cursor += 1
            dirty  = True
            count  += 1

        # printable character: insert at cursor
        elif 32 <= val <= 126:
            text   = text[:cursor] + chr(val) + text[cursor:]
            cursor += 1
            dirty  = True
            count  += 1

        # refresh display
        # full refresh every 200 keypresses to clear ghosting
        # partial refresh for all other updates (fast, no flicker)
        if count >= 200:
            scroll = draw_edit(text, cursor, scroll, fname, dirty)
            full_refresh()
            count = 0
        else:
            scroll = draw_edit(text, cursor, scroll, fname, dirty)
            partial_refresh()

        time.sleep(0.01)


# entry point

if __name__ == '__main__':
    home_screen()
