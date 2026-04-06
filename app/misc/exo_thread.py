import random
import asyncio

POOL_SIZE = 3
PRODUCTION_STOPPED = False
queue = []
display_queue = lambda q : [q[i]["message_id"] for i in range(len(q))]

async def producer():
    global PRODUCTION_STOPPED
    print(f"Producer__ : start")
    for i in range(10):
        queue.append({
            "message_id": i,
            "payload": round(random.random(), 2)
        })
        print(f"Producer__ : +", display_queue(queue)) 
        await asyncio.sleep(.25)
    PRODUCTION_STOPPED = True
    print(f"Producer__ : end")
async def consume(id):
    print(f"consumer {id} : start")
    global queue, loop
    while 1 : 
        await asyncio.sleep(random.random())
        print(f"Consumer {id} : +", display_queue(queue))   
        if len(queue) > 0 :
            current_message_id, current_sleep_time = queue[0].values()
            queue = queue[1:]
            await asyncio.sleep(current_sleep_time)
            print(f"Consumer {id} : - [{current_message_id}]")
        else:
            if PRODUCTION_STOPPED:
                print(f"Consumer {id} : end")
                break
async def pubsub():
    asyncio.get_event_loop().create_task(producer())
    for i in range(POOL_SIZE):
        asyncio.get_event_loop().create_task(consume(i))
try:
    loop = asyncio.get_event_loop()
    asyncio.run_coroutine_threadsafe(pubsub(), loop)
except KeyboardInterrupt:
    pass