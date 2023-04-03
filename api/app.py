from client import LocationKeyClient

import asyncio
import random

client = LocationKeyClient(url= "http://192.168.1.169:8085")

async def my_async_function():    
    print("Running request...")
    
    client.location(hex(random.randint(0, 256)))

    

async def my_infinite_loop():
    while True:
        wait_time = random.uniform(0, 10)
        await asyncio.sleep(wait_time)
        asyncio.create_task(my_async_function())

asyncio.run(my_infinite_loop())