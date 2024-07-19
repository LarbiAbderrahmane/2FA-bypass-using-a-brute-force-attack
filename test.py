from classes.Monitor import Monitor
import asyncio

# shared = Monitor()


async def job_1():
    print("job-1")
        # await asyncio.sleep(.5)
        
async def job_2():
    print("job-2")
        # await asyncio.sleep(.5)
async def job_3():
    raise Exception()
    print("job-3")
    
async def job_4():
    raise Exception()
    print("job-4")
    
async def job_5():
    print("job-5")
    raise Exception()
        


async def main():
    t1 = asyncio.create_task(job_1())
    t2 = asyncio.create_task(job_2())
    t3 = asyncio.create_task(job_3())
    t4 = asyncio.create_task(job_4())
    t5 = asyncio.create_task(job_5())

    await t1
    await t2
    
    try:
        await asyncio.gather(*[t3, t4, t5])
    except(Exception):
        print("error")
    
asyncio.run(main())
    