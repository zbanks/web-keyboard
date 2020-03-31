#!/usr/bin/env python3

# Based on "Synchronization example" from websockets example code
# https://websockets.readthedocs.io/en/stable/intro.html#synchronization-example

import asyncio
import json
import logging
import websockets

logging.basicConfig()

VERSION = 1
KEYS = ["a", "b", "left", "up", "down", "right"]

WELCOME = {
    "version": VERSION,
    "keys": KEYS,
}
USERS = {}

def key_states():
    return [any(xs) for xs in zip(*USERS.values())]

def welcome_event():
    return json.dumps(WELCOME)

def state_event():
    return json.dumps({
        "u": len(USERS),
        "k": key_states(),
    })

async def notify_state():
    if USERS:  # asyncio.wait doesn't accept an empty list
        message = state_event()
        print(message)
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


start_server = websockets.serve(counter, "localhost", 6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
