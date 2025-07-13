#!/usr/bin/env python3
import subprocess
import signal
import time
import sys
import threading
import re
import os

# Shared state
extend_minutes = 0
exit_requested = False

def run_pmset(value):
    """Run pmset to (dis)allow sleep."""
    try:
        subprocess.run(['pmset', '-a', 'disablesleep', value], check=True)
    except subprocess.CalledProcessError:
        print(f"Failed to set disablesleep {value}")
        sys.exit(1)

def notify(message):
    # Get current time in HH:MM:SS format
    timestamp = time.strftime("%H:%M:%S")
    message = f"{message} (Notified at {timestamp})"

    # macOS visual notification
    subprocess.run([
        'osascript',
        '-e', f'display notification "{message}" with title "NoSleep"'
    ])

    # Play sound 4 times, every 0.5s
    for _ in range(4):
        subprocess.Popen(['afplay', '/System/Library/Sounds/Glass.aiff'])
        time.sleep(0.5)

def get_battery_percent():
    try:
        output = subprocess.check_output(['pmset', '-g', 'batt']).decode()
        percent_str = output.split('\t')[1].split(';')[0].strip()
        return int(percent_str.replace('%', ''))
    except Exception:
        return 100  # Fail-safe default

def input_listener():
    global extend_minutes
    while not exit_requested:
        user_input = input().strip()
        match = re.match(r'^e\s+(\d+)$', user_input, re.IGNORECASE)
        if match:
            extra = int(match.group(1))
            if extra > 0:
                extend_minutes += extra * 60
                print(f"Extension requested: +{extra} minutes.")

def cleanup():
    print("\nRe-enabling sleep (disablesleep 0).")
    run_pmset('0')

def signal_handler(signum, frame):
    global exit_requested
    exit_requested = True
    cleanup()
    sys.exit(0)

def main():
    global extend_minutes

    if os.geteuid() != 0:
        print("In order to ensure default sleep behavior is always restored, please run this script with sudo:")
        print("  sudo ./nosleep.py <minutes>")
        sys.exit(1)

    if len(sys.argv) != 2:
        print("Usage: stayawake.py <minutes>")
        sys.exit(1)

    try:
        minutes = int(sys.argv[1])
        if minutes < 2:
            raise ValueError
    except ValueError:
        print("Please provide a valid number of minutes (minimum 2).")
        sys.exit(1)

    # Signal traps
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Clean state: re-enable sleep before starting
    print("Ensuring default sleep behavior before starting...")
    run_pmset('0')

    # Disable sleep for the session
    print("Disabling sleep (disablesleep 1)...")
    run_pmset('1')

    start = time.time()
    duration = minutes * 60
    end_timestamp = start + duration
    sleep_time = time.strftime("%H:%M", time.localtime(end_timestamp))

    print(f"\nSleep disabled for {minutes} minutes.")
    curr_time = time.strftime("%H:%M", time.localtime(start))
    print(f"Current time: {curr_time}")
    print(f"Planned sleep time: {sleep_time}")
    print("Type `e <N>` + Enter anytime to extend by N more minutes (e.g. `e 5`).\n")

    threading.Thread(target=input_listener, daemon=True).start()

    notified_low_battery = False
    notified_2min_timer = False
    notified_5min_timer = False

    try:
        while time.time() - start < duration:
            remaining = duration - (time.time() - start)

            # Low battery alert
            if not notified_low_battery:
                output = subprocess.check_output(['pmset', '-g', 'batt']).decode()
                if "AC Power" in output:
                    continue
                battery = get_battery_percent()
                if battery < 20:
                    notify("Battery < 20%. Sleeping in 2 mins unless plugged in.")
                    notified_low_battery = True
                    time.sleep(120)
                    output = subprocess.check_output(['pmset', '-g', 'batt']).decode()
                    if "AC Power" not in output:
                        cleanup()
                        subprocess.run(['pmset', 'sleepnow'])
                        sys.exit(0)
                    else:
                        notified_low_battery = False
                        print("AC power detected. Cancelled auto-sleep.")
                    break

            # 5-minute warning
            if not notified_5min_timer and remaining <= 300:
                notify("5 minutes left. Type `e <N>` to extend.")
                notified_5min_timer = True

            # 2-minute warning
            if not notified_2min_timer and remaining <= 120:
                notify("2 minutes left. Type `e <N>` to extend.")
                notified_2min_timer = True

            # Apply extensions
            if extend_minutes > 0:
                added_minutes = extend_minutes // 60
                duration += extend_minutes
                new_sleep_time = time.strftime("%H:%M", time.localtime(start + duration))
                print(f"Extended by {added_minutes} minutes. New sleep time: {new_sleep_time}")
                extend_minutes = 0
                notified_2min_timer = False
                notified_5min_timer = False

            time.sleep(30) # sleep a while

    finally:
        cleanup()

if __name__ == "__main__":
    main()
