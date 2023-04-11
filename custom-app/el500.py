import numpy as np
import time
import collections
import threading
import csv
import matplotlib.pyplot as plt
from main import El500Cmd
import webapp


class El500:
    def __init__(self, queue_size=100):
        self.state_queue = collections.deque(maxlen=queue_size)
        self.session_log = collections.deque()
        self.last_saved_state = None
        self.init_variables()

    def init_variables(self):
        self.equipment_id = None
        self.serial_number = None
        self.version = None
        self.usage_hours = None
        self.cumulative_km = None
        self.display_mode = None
        self.distance = None
        self.kmph = None
        self.rpm = None
        self.resistance = None
        self.heart_rate = None
        self.kcal = None
        self.incline_percent = None
        self.mwatt = None
        self.heart_rate_led_color = None
        self.bt_led_switch = None
        self.fan_speed = None
        self.hot_key = None

    def update_state(self, cmd_id, response):
        if cmd_id == El500Cmd.getEquipmentId:
            self.equipment_id = response
        elif cmd_id == El500Cmd.getSerialNumber:
            self.serial_number = response
        elif cmd_id == El500Cmd.getVersion:
            self.version = response
        elif cmd_id == El500Cmd.getUsageHours:
            self.usage_hours = response
        elif cmd_id == El500Cmd.getCumulativeKm:
            self.cumulative_km = response
        elif cmd_id == El500Cmd.setDisplay:
            (
                self.display_mode,
                self.distance,
                self.kmph,
                self.rpm,
                self.resistance,
                self.heart_rate,
                self.kcal,
            ) = response
        elif cmd_id == El500Cmd.setInfoValue:
            (
                self.kmph,
                self.resistance,
                self.incline_percent,
                self.mwatt,
                self.heart_rate_led_color,
                self.bt_led_switch,
            ) = response
        elif cmd_id == El500Cmd.setFanSpeed:
            self.fan_speed = response
        elif cmd_id == El500Cmd.setHotKey:
            self.hot_key = response

    def update_state_from_mock_data(self, cmd_id, response):
        # self.update_state(cmd_id, response)
        # self.state_queue.append((time.time(), self.get_state()))
        if cmd_id == b"\xAD":
            kmph = response[4:6]
            resistance = response[8]
            self.kmph = int.from_bytes(kmph, byteorder="big", signed=True)
            self.resistance = resistance
        self.state_queue.append((time.time(), self.get_state()))

    def get_state(self):
        return {
            "kmph": self.kmph,
            "resistance": self.resistance,
        }

    def update_plot(self):
        speeds = []
        resistances = []
        for state in self.state_queue:
            _, device_state = state
            speeds.append(device_state["kmph"])
            resistances.append(device_state["resistance"])
        plt.plot(speeds, label="Speed (kmph)")
        plt.plot(resistances, label="Resistance")
        plt.xlabel("Time")
        plt.ylabel("Value")
        plt.legend()
        plt.show()

    def update_session_log(self):
        current_state = self.get_state()
        if self.last_saved_state != current_state:
            self.last_saved_state = current_state
            self.session_log.append((time.time(), current_state))

    def save_session_log_to_csv(self, filename="session_log.csv"):
        with open(filename, "w", newline="") as csvfile:
            fieldnames = ["timestamp", "kmph", "resistance"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for entry in self.session_log:
                timestamp, state = entry
                writer.writerow(
                    {
                        "timestamp": timestamp,
                        "kmph": state["kmph"],
                        "resistance": state["resistance"],
                    }
                )

    def send_and_update_state(self, cmd_id, payload=None, timeout=1, attempts=1):
        response = El500Cmd.send(cmd_id, payload, timeout, attempts)
        self.update_state(cmd_id, response)
        self.state_queue.append((time.time(), self.get_state()))
        webapp.data_queue.put({"timestamp": time.time(), "kmph": kmph, "resistance": resistance})


if __name__ == "__main__":
    killallthreads = False
    def devlogic():
        el500 = El500()

        for i in range(200):
            if killallthreads is True:
                break
            cmd_id = b"\xAD"
            kmph = np.random.randint(0, 30)
            resistance = np.random.randint(0, 10)
            response = b"\xff" * 4 + np.int8(kmph).tobytes() + b"\xff" * 2 + np.int8(resistance).tobytes() + b"\xff" * 6
            el500.update_state_from_mock_data(cmd_id, response)
            time.sleep(0.25)
    
    try:
        # start devlogic thread
        threading.Thread(target=devlogic).start()
        webapp.run_app()
    finally:
        killallthreads = True
        time.sleep(0.6)
