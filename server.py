#!/usr/bin/env python3

# Based on "Synchronization example" from websockets example code
# https://websockets.readthedocs.io/en/stable/intro.html#synchronization-example

import asyncio
import json
import logging
import websockets
import evdev

logging.basicConfig()

VERSION = 1

KEYS = [
    ("a", evdev.ecodes.KEY_A),
    ("b", evdev.ecodes.KEY_B),
    #("l", evdev.ecodes.KEY_C),
    #("r", evdev.ecodes.KEY_D),
    ("left", evdev.ecodes.KEY_LEFT),
    ("right", evdev.ecodes.KEY_RIGHT),
    ("up", evdev.ecodes.KEY_UP),
    ("down", evdev.ecodes.KEY_DOWN),
    ("start", evdev.ecodes.KEY_E),
    ("select", evdev.ecodes.KEY_F),
    ("turbo", evdev.ecodes.KEY_G),
]

WELCOME = {
    "version": VERSION,
    "keys": [n for n, c in KEYS]
}
USERS = {}
UINPUT = evdev.UInput()

def key_states():
    return [sum(xs) for xs in zip([False for x in KEYS], *USERS.values())]

def welcome_event():
    return json.dumps(WELCOME)

def state_event():
    return json.dumps({
        "u": len(USERS),
        "k": key_states(),
    })

async def notify_state():
    for (_name, code), v in zip(KEYS, key_states()):
        UINPUT.write(evdev.ecodes.EV_KEY, code, bool(v))
    UINPUT.syn()

    if USERS:  # asyncio.wait doesn't accept an empty list
        message = state_event()
        await asyncio.wait([user.send(message) for user in USERS])

async def counter(websocket, path):
    await websocket.send(welcome_event())

    USERS[websocket] = [False for x in KEYS]
    try:
        while True:
            await notify_state()

            message = await websocket.recv()
            data = json.loads(message)
            bool_data = [bool(x) for x in data]
            if len(bool_data) == len(KEYS):
                USERS[websocket] = bool_data
            else:
                logging.error("unsupported event: {}", message)
    finally:
        USERS.pop(websocket)
        await notify_state()


start_server = websockets.serve(counter, "0.0.0.0", 6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
