import filecmp
import importlib.resources
import os
import shutil
from .parse import Arguments, HandlerType
from pathlib import Path
import datamodel_code_generator as dmcg
import importlib

def _check_dir_conflicts(dir1: Path | str, dir2: Path | str):
    dir_comp = filecmp.dircmp(dir1, dir2)
    if dir_comp.common_files:
        print(f"WARNING: Common files in {dir1} and {dir2}: {dir_comp.common_files}")
        return False
    for common_dir in dir_comp.common_dirs:
        if not _check_dir_conflicts(
            os.path.join(dir1, common_dir), os.path.join(dir2, common_dir)
        ):
            return False
    return True


def generate_template_repo(args: Arguments):
    if not os.path.exists(args.output_dir):
        os.mkdir(args.output_dir)
    # 使用 importlib.resources 来访问内置的模板文件夹
    print(f"Start to generate template repo in {args.output_dir}") 
    with importlib.resources.path(
        "spirit_gpu.resources", "worker-template"
    ) as template_path:
        if not _check_dir_conflicts(template_path, args.output_dir):
            raise ValueError(
                f"Output directory {args.output_dir} contains files that conflict with generated files. Please remove them or specify a different output directory."
            )
        shutil.copytree(template_path, args.output_dir, dirs_exist_ok=True)
    print("Template repo generated\n")


def _get_model_path(output_dir: str) -> Path:
    return Path(os.path.join(output_dir, "src", "spirit_generated_model.py")).absolute()


def generate_model_file(args: Arguments):
    input_file = Path(args.input_file).absolute()
    output_file = Path(_get_model_path(args.output_dir)).absolute()
    print(f"Start to generate model file, input: {input_file}, output: {output_file}")
    dmcg.generate(
        input_file.read_text(),
        input_file_type=args.input_type,
        input_filename=input_file.name,
        output=output_file,
        output_model_type=args.data_type,
        class_name="RequestInput",
    )
    print("Model file generated\n")


def _get_main_path(output_dir: str) -> Path:
    return Path(os.path.join(output_dir, "src", "main.py")).absolute()


def generate_main_file(args: Arguments):
    output_file = Path(_get_main_path(args.output_dir)).absolute()
    print(f"Start to generate main file, output: {output_file}")
    output = _generate_main_import(args)
    output += _generate_main_request_input(args)
    output += _generate_main_handler(args)
    output += _generate_main_other(args)
    output_file.write_text(output)
    print("Main file generated\n")


IMPORTS = """
from typing import Any, Dict

from spirit_gpu import start, logger
from spirit_gpu.env import Env
from spirit_generated_model import RequestInput

"""


def _generate_main_import(args: Arguments):
    if args.data_type == dmcg.DataModelType.DataclassesDataclass:
        return IMPORTS + "import dacite\n"
    return IMPORTS


REQUEST_INPUT_FROM_DATACLASS = """
def get_request_input(request: Dict[str, Any]) -> RequestInput:
    return dacite.from_dict(RequestInput, request["input"])
"""

REQUEST_INPUT_FROM_PYDANTIC = """
def get_request_input(request: Dict[str, Any]) -> RequestInput:
    return RequestInput(**request["input"])
"""


def _generate_main_request_input(args: Arguments):
    dt = args.data_type
    if dt == dmcg.DataModelType.DataclassesDataclass:
        return REQUEST_INPUT_FROM_DATACLASS
    elif dt == dmcg.DataModelType.PydanticV2BaseModel:
        return REQUEST_INPUT_FROM_PYDANTIC
    else:
        raise ValueError(f"Unsupported data type: {dt}")


HANDLER_SYNC = """
def handler_impl(request_input: RequestInput, request: Dict[str, Any], env: Env):
    \"\"\"
    Your handler implementation goes here.
    \"\"\"
    pass

def handler(request: Dict[str, Any], env: Env):
    request_input = get_request_input(request)
    return handler_impl(request_input, request, env)
"""

HANDLER_ASYNC = """
async def handler_impl(request_input: RequestInput, request: Dict[str, Any], env: Env):
    \"\"\"
    Your handler implementation goes here.
    \"\"\"
    pass
    
async def handler(request: Dict[str, Any], env: Env):
    request_input = get_request_input(request)
    return await handler_impl(request_input, request, env)
"""

HANDLER_SYNC_GEN = """
def handler_impl(request_input: RequestInput, request: Dict[str, Any], env: Env):
    \"\"\"
    Your handler implementation goes here.
    \"\"\"
    yield None

def handler(request: Dict[str, Any], env: Env):
    request_input = get_request_input(request)
    for output in handler_impl(request_input, request, env):
        yield output
"""

HANDLER_ASYNC_GEN = """
async def handler_impl(request_input: RequestInput, request: Dict[str, Any], env: Env):
    \"\"\"
    Your handler implementation goes here.
    \"\"\"
    yield None

async def handler(request: Dict[str, Any], env: Env):
    request_input = get_request_input(request)
    async for output in handler_impl(request_input, request, env):
        yield output
"""


def _generate_main_handler(args: Arguments):
    ht = args.handler_type
    if ht == HandlerType.Sync:
        return HANDLER_SYNC
    elif ht == HandlerType.Async:
        return HANDLER_ASYNC
    elif ht == HandlerType.SyncGenerator:
        return HANDLER_SYNC_GEN
    elif ht == HandlerType.AsyncGenerator:
        return HANDLER_ASYNC_GEN
    else:
        raise ValueError(f"Unsupported handler type: {ht}")


OTHER = """
def concurrency_modifier(current_concurrency: int) -> int:
    \"\"\"
    Allow 5 job to run concurrently.
    Be careful with this function.
    You should fully understand python GIL and related problems before setting this value bigger than 1.
    \"\"\"
    return 1

# Start the serverless function
logger.info("start to run handler.")
start({"handler": handler, "concurrency_modifier": concurrency_modifier})
"""


def _generate_main_other(args: Arguments):
    return OTHER
