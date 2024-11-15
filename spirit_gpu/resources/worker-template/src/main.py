import asyncio
from time import sleep
from typing import Any, Dict

from spirit_gpu import start, logger
from spirit_gpu.env import Env


def concurrency_modifier(current_concurrency: int) -> int:
    """
    Allow 5 job to run concurrently.
    Be careful with this function.
    You should fully understand python GIL and related problems before setting this value bigger than 1.
    """
    return 1


async def async_handler(request: Dict[str, Any], env: Env):
    output = f"hello world! {request}"
    await asyncio.sleep(0.1)
    return bytes(output, "utf-8")


async def async_gen_handler(request: Dict[str, Any], env: Env):
    output = f"hello world! {request}"
    for i in range(10):
        await asyncio.sleep(0.01)
        yield f"{output} - {i}\n"


def gen_handler(request: Dict[str, Any], env: Env):
    output = f"hello world! {request}"
    for i in range(10):
        sleep(0.01)
        yield f"{output} - {i}\n"


def handler(request: Dict[str, Any], env: Env):
    # please use latest version of spirit_gpu, we will only add request["meta"]["requestID"] if it not exist in your request.
    request_id = request["meta"]["requestID"]
    logger.info("start to handle", request_id=request_id, caller=True)

    output = f"hello world! {request}"
    sleep(0.1)
    return bytes(output, "utf-8")


# Start the serverless function
# start({"handler": async_handler, "concurrency_modifier": concurrency_modifier})
# start({"handler": async_gen_handler, "concurrency_modifier": concurrency_modifier})
# start({"handler": gen_handler, "concurrency_modifier": concurrency_modifier})
start({"handler": handler, "concurrency_modifier": concurrency_modifier})
