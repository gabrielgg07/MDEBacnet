#!/usr/bin/env python2

import time
import argparse
import Tkinter as tk
import socket
import json


LEVEL_SENSOR_FD = "CB7 Analog In 04  Mon"
PRESS_SENSOR_FD = "CB7 Analog In 05  Mon"

VENT_OPEN_SW_FD   = "CB7 Discrete In 03  Ind"
VENT_CLOSE_SW_FD  = "CB7 Discrete In 04  Ind"
PRESS_OPEN_SW_FD  = "CB7 Discrete In 01  Ind"
PRESS_CLOSE_SW_FD = "CB7 Discrete In 02  Ind"

LEVEL_SENSOR_RANGE = 600.0
PRESS_SENSOR_RANGE = 300
MAX_SCALE = 30000
LN2_SPECIFIC_GRAVITY = 0.808

SWITCH_MEAS_TRANS = {
    "true": True,
    "false": False,
    "1": True,
    "0": False
}

class MonitorModel(object):
    def __init__(self):
        self.level = 0.0
        self.pressure = 0.0
        self.delta_p = 0.0
        self.vent_open = False
        self.vent_close = True
        self.press_open = False
        self.press_close = True

    def parse_switch(self, val):
        return SWITCH_MEAS_TRANS.get(val.strip().lower(), False)

    def parse_analog(self, val):
        try:
            return float(val)
        except:
            return None

    def set_level(self, raw):
        val = self.parse_analog(raw)
        if val is None:
            return
        self.delta_p = val * LEVEL_SENSOR_RANGE / MAX_SCALE
        self.level = self.delta_p / LN2_SPECIFIC_GRAVITY

    def set_pressure(self, raw):
        val = self.parse_analog(raw)
        if val is None:
            return
        self.pressure = val * PRESS_SENSOR_RANGE / MAX_SCALE

class Monitor(object):
    def __init__(self):
        import simulator

        self.model = MonitorModel()
        self.root = tk.Tk()
        self.root.title("LN2 Monitor")

        # attach simulator GUI
        self.iface = simulator.Simulator(
            standalone=False,
            main_window=self.root
        )

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(1.0)
        self.sock.connect(("10.97.0.130", 9000))
        # start polling
        self.root.after(500, self.poll)
        self.root.after(500, self.publish)

    def poll(self):
        self.model.set_level(self.iface.GetMeasValue(LEVEL_SENSOR_FD))
        self.model.set_pressure(self.iface.GetMeasValue(PRESS_SENSOR_FD))

        self.model.vent_open  = self.model.parse_switch(self.iface.GetMeasValue(VENT_OPEN_SW_FD))
        self.model.vent_close = self.model.parse_switch(self.iface.GetMeasValue(VENT_CLOSE_SW_FD))
        self.model.press_open = self.model.parse_switch(self.iface.GetMeasValue(PRESS_OPEN_SW_FD))
        self.model.press_close= self.model.parse_switch(self.iface.GetMeasValue(PRESS_CLOSE_SW_FD))



        # reschedule
        self.root.after(500, self.poll)

    def publish(self):
        snapshot = {
            "pressure": self.model.pressure,
            "level": self.model.level,
            "delta_p": self.model.delta_p,
            "vent_open": self.model.vent_open,
            "vent_close": self.model.vent_close,
            "press_open": self.model.press_open,
            "press_close": self.model.press_close,
        }

        print(
            "Pressure: %.2f psig | Level: %.2f in | dP: %.2f inH2O | "
            "Vent(O/C): %s/%s | Supply(O/C): %s/%s"
            % (
                self.model.pressure,
                self.model.level,
                self.model.delta_p,
                self.model.vent_open,
                self.model.vent_close,
                self.model.press_open,
                self.model.press_close,
            )
        )

        payload = json.dumps(snapshot) + "\n"
        try:
            self.sock.sendall(payload)
        except socket.error:
            # handle reconnect or drop
            pass


        self.root.after(500, self.publish)


    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    m = Monitor()
    m.run()
