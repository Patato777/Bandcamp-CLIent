from pynput import keyboard
import time,sys

def on_press(key):
    try:
        if key.char == 'a' :
            print('Ca marche !')
        if key.char == '/' :
            print('Meme en majuscules !')
        print('alphanumeric key {0} pressed'.format(
            key.char))
    except AttributeError:
        print('special key {0} pressed'.format(
            key))

def on_release(key):
    print('{0} released'.format(
        key))
    if key == keyboard.Key.esc:
        # Stop listener
        return False

# Collect events until released
listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release)
listener.start()

while True :
    time.sleep(1)
