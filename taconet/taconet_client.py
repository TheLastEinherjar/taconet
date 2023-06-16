import socket
import json
import threading
import curses
from math import sin, pi
from unicorn_text import Unicorn

class RainbowText:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.default_frequency = 220
        self.supports_color = curses.can_change_color()

    def rainbow(self, frequency, i):
        """Creates RGB values, inspired from https://github.com/busyloop/lolcat
        
        Args:
            freq (int): Frequency, more the value; more the colours
            i (int): Current character position, used to set colours at character level
        
        Returns:
            tuple: Contains integers R, G, B
        """
        red = sin(frequency * i + 0) * 127 + 128
        green = sin(frequency * i + 2*pi/3) * 127 + 128
        blue = sin(frequency * i + 4*pi/3) * 127 + 128
        # return "%0x"%(int(red)), "%0x"%(int(green)), "%0x"%(int(blue))
        return int(red), int(green), int(blue)

    def get_rainbow_text(self, text, frequency=-1):
        if frequency == -1:
            frequency = self.default_frequency
        rainbow_text = []
        if not self.supports_color:
            for letter in text:
                rainbow_text.append(letter)
        else:
            for i, c in enumerate(text):
                r, g, b = self.rainbow(frequency, i)
                color_id = 8 + i
                # Define new color
                curses.init_color(color_id, r * 1000 // 255, g * 1000 // 255, b * 1000 // 255)
                # Define new color pair
                curses.init_pair(color_id, color_id, curses.COLOR_BLACK)
                # Apply the color pair to the text
                rainbow_text.append((c, curses.color_pair(color_id)))
        return rainbow_text
    
def main(stdscr):
    global standard_screen, rt
    # Set up the screen
    stdscr = curses.initscr()
    curses.noecho()
    stdscr.keypad(True)
    curses.curs_set(0)  # Show cursor
    stdscr.nodelay(1)  # Set getch() to non-blocking
    stdscr.timeout(100)  # Refresh every 100ms

    # Create windows for messages and input
    global message_window, input_window
    message_window = curses.newwin(curses.LINES - 5, curses.COLS, 0, 0)
    input_window = curses.newwin(4, curses.COLS, curses.LINES - 4, 0)

    message_window.scrollok(True) # Enable scrolling in message window
    curses.start_color()
    standard_screen = stdscr
    rt = RainbowText(stdscr)

def print_message(message) :
    global message_window
    rainbow_text = rt.get_rainbow_text(message)
    for i, (char, color) in enumerate(rainbow_text):
        y_pos, x_pos = message_window.getyx()
        rows, cols = message_window.getmaxyx()
        if x_pos < cols - 1:  # Check if we are not out of columns
            message_window.addstr(y_pos, x_pos, char, color)
        else:
            # Make a new line
            y_pos += 1
            x_pos = 0
            message_window.addstr(y_pos, x_pos, char, color)
    message_window.addstr("\n")
    message_window.addstr("\n")
    message_window.refresh()

def message_input():
    global standard_screen, input_window
    message = ''
    while True:
        # Handle user input
        ch = standard_screen.getch()
        if ch == ord("\n"):  # Enter key
            # Send the message
            return message
        elif ch == curses.KEY_BACKSPACE :
            message = message[:-1]
        elif ch != -1:
            message += chr(ch)

        input_window.clear()
        rainbow_text = rt.get_rainbow_text(f"Your Message: {message}")
        for i, (char, color) in enumerate(rainbow_text):
            y_pos, x_pos = input_window.getyx()
            rows, cols = input_window.getmaxyx()
            if x_pos < cols - 1:  # Check if we are not out of columns
                input_window.addstr(y_pos, x_pos, char, color)
            else:
                # Make a new line
                y_pos += 1
                x_pos = 0
                input_window.addstr(y_pos, x_pos, char, color)

        input_window.refresh()


def send_messages() :
    global remain_open
    while remain_open :
        # Prompt the user for a message
        message = message_input()

        if message[0] != '-' :
            # Create a JSON object with the username and message
            data = {'name': username, 'message': message}
            json_data = json.dumps(data)

            # Send the JSON string to the server
            sock.sendall(json_data.encode('utf-8'))
        else :
            match message :
                case '-close' :
                    close_message = json.dumps({'name': username, 'message': '-close'})
                    sock.sendall(close_message.encode('utf-8'))
                    try :
                        sock.close()
                    except :
                        pass
                    remain_open = False

# Prompt the user for the socket address and username
socket_address = input("Enter the socket address [255.255.255.255:7800]: ")
socket_ip, port = socket_address.split(':')
username = input("Enter your username: ")
remain_open = True

# Create a socket connection
sock = socket.socket() # Same API as socket.socket in the standard lib
sock.connect((socket_ip, int(port)))

curses.wrapper(main)

threading.Thread(target=send_messages, daemon=True).start()

while remain_open:
    # Wait for a response from the server
    received_data = sock.recv(1024)
    received_json = received_data.decode()
    received_data = json.loads(received_json)

    # Print the received message
    print_message(f"{received_data['name']}: {received_data['message']}")
    
sock.close()