import socket
import threading
import json, os, tempfile

# GLOBAL sensor value cache
sensor_cache = {
    "AI1": None,
    "AI2": None,
    "AI3": None,
    # ...
}

DATA_PATH = "/tmp/padA_state.json"

def write_data(data):
    dir_path = os.path.dirname(DATA_PATH)
    with tempfile.NamedTemporaryFile(
        mode="w",
        dir=dir_path,
        delete=False
    ) as tmp:
        json.dump(data, tmp)
        tmp.flush()
        os.fsync(tmp.fileno())

    os.replace(tmp.name, DATA_PATH)  # atomic

def tcp_listener():
    dir_path = "/tmp"
    #tmp = tempfile.NamedTemporaryFile(delete=False, dir=dir_path)
    
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
        decoded = pkt.decode("utf-8").strip()
        data = json.loads(decoded)   # bytes → dict
        print(data)
        write_data(data)

       

if __name__ == "__main__":
    tcp_listener()
    #threading.Thread(target=tcp_listener, daemon=True).start()

b'{"vent_open": false, "vent_close": true, "level": 393.1188118811881, "press_open": false, "delta_p": 317.64, "pressure": 0.0, "press_close": true}\n'
b'{"vent_open": false, "vent_close": true, "level": 393.1188118811881, "press_open": false, "delta_p": 317.64, "pressure": 0.0, "press_close": true}\n'
b'{"vent_open": false, "vent_close": true, "level": 393.1188118811881, "press_open": false, "delta_p": 317.64, "pressure": 0.0, "press_close": true}\n'