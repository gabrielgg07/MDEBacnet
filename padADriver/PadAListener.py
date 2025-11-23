import socket
import threading

# GLOBAL sensor value cache
sensor_cache = {
    "AI1": None,
    "AI2": None,
    "AI3": None,
    # ...
}


def tcp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", 9000))   # or whatever port
    sock.listen(1)
    print("TCP listener waiting for PoD-A connection...")

    conn, addr = sock.accept()
    print(f"TCP connected: {addr}")

    while True:
        pkt = conn.recv(1024)
        if not pkt:
            break

        # TODO: decode your custom packet
        # Example (fake):
        # AI1|23.5\nAI2|99.1\nAI3|53.2\n
        lines = pkt.decode().strip().split("\n")
        for line in lines:
            key, val = line.split("|")
            sensor_cache[key] = float(val)

threading.Thread(target=tcp_listener, daemon=True).start()
