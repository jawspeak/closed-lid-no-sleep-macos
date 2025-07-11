# Purpose

This lets you have your macbook clamshell lid closed but not go to sleep. Useful if you have an external monitor and you want to use it. Works even if no AC power is connected.

Similar to Amphetamine.app in the app store, but more bare bones. That app worked, but Caffeine.app, `caffeinate`, and another one tested did not work when clamshell closed and no AC power attached. This works.

Features:

- Run this command line tool with N minutes you want to not-sleep
- When that time runs out it will let your mac sleep again
- If battery is below 20% it will give a notification and then allow sleeping after 120 seconds to give you a chance to plug in
- 2 minutes before the timer is up, there is a notification reminding you your session is ending
- Notifications also play a sound
- At any time you can extend in the menu of the command line tool that is running
- If the command line tool receives a signal to quit gracefully, it tries to restore the default sleep behavior
- When I terminate the tool it should set it to the default (that it will sleep). Also at startup it sets it to that default behavior.


Usage:

`./nosleep.py 20`

See what the current sleep settings are with: `pmset -g`

Implementation:

- Prevents sleep by running `sudo pmset -a disablesleep 0`
- Enables sleep by running `sudo pmset -a disablesleep 1`
