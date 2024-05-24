# gcodeToIselCPM
This project aims to translate G-code commands into commands understood by an Isel CPM CNC machine. It reads G-code from a file, processes it to extract relevant instructions, and sends them to the CNC machine via a serial connection. The system also handles error responses from the machine.

WARNING: This code is provided "as is", without any warranty. Use it at your own risk.

# CNC Interface

This is a graphical user interface (GUI) for controlling a CNC machine using Python's `tkinter` library.

## Features

- Move the CNC machine in X, Y, and Z directions.
- Set the home position and define a zero point.
- Load and execute GCode files.
- Start and stop the tool.
- Display messages and progress.

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/PaulQuiDev/gcodeToIselCPM
   ```
