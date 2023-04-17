
import os
from concurrent.futures import ThreadPoolExecutor
from client import AirAnchorClient

from random import randint, random
from time import sleep
from pyrate_limiter import Duration, RequestRate, Limiter

client = AirAnchorClient(rabbitmq_url='192.168.1.169', priv_path="priv.key")
leaky_bucket = Limiter(RequestRate(limit=40, interval=Duration.SECOND))
count = 0

@leaky_bucket.ratelimit('bucket', delay=True)
def _work():
    global count
    count += 1
    print("sending transaction: {}".format(count))
    client.do_location(hex(randint(0, 2 ** 256)))

with ThreadPoolExecutor() as executor:
    while True:
        _work()
        
