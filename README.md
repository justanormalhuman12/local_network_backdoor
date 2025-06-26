# Python TCP Socket Application

This project demonstrates a simple client-server architecture using TCP sockets in Python. The server (`host.py`) listens for incoming connections from clients (`slave.py`) and executes instructions sent by the client.

## Project Structure

- `host.py`: The server application that handles incoming client connections and executes commands.
- `slave.py`: The client application that connects to the server and sends commands for execution.

## Requirements

- Python 3.x
- No additional libraries are required as this project uses built-in Python libraries.

## How to Run

1. Start the server:
   - Open a terminal and navigate to the project directory.
   - Run the command: `python host.py`

2. Start the client:
   - Open another terminal and navigate to the project directory.
   - Run the command: `python slave.py`

3. Follow the prompts in the client to send commands to the server.

## Example Usage

- The client can send commands like `ls`, `pwd`, or any other shell command supported by the server's operating system.
- The server will execute the command and return the output back to the client.

## Notes

- Ensure that the server is running before starting the client.
- This project is intended for educational purposes and should not be used in production environments without proper security measures.