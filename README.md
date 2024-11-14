# Spirit-GPU

- [Spirit-GPU](#spirit-gpu)
  - [Install](#install)
  - [Usage example](#usage-example)
  - [Logging](#logging)
  - [API](#api)
  - [Builder](#builder)

## Install
```
pip install spirit-gpu
```

## Usage example

```python
from spirit_gpu import start
from spirit_gpu.env import Env
from typing import Dict, Any

def handler(request: Dict[str, Any], env: Env):
    """
    request: Dict[str, Any], from client http request body.
    request["input"]: Required.
    request["webhook"]: Optional string for asynchronous requests.

    returned object to be serialized into JSON and sent to the client.
    in this case: '{"output": "hello"}'
    """
    return {"output": "hello"}


def gen_handler(request: Dict[str, Any], env: Env):
    """
    append yield output to array, serialize into JSON and send to client.
    in this case: [0, 1, 2, 3, 4]
    """
    for i in range(5):
        yield i


async def async_handler(request: Dict[str, Any], env: Env):
    """
    returned object to be serialized into JSON and sent to the client.
    """
    return {"output": "hello"}


async def async_gen_handler(request: Dict[str, Any], env: Env):
    """
    append yield output to array, serialize into JSON and send to client.
    """
    for i in range(10):
        yield i


def concurrency_modifier(current_allowed_concurrency: int) -> int:
    """
    Adjusts the allowed concurrency level based on the current state.
    For example, if the current allowed concurrency is 3 and resources are sufficient,
    it can be increased to 5, allowing 5 tasks to run concurrently.
    """
    allowed_concurrency = ...
    return allowed_concurrency


"""
Register the handler with serverless.start().
Handlers can be synchronous, asynchronous, generators, or asynchronous generators.
"""
start({
    "handler": async_handler, "concurrency_modifier": concurrency_modifier
})
```

## Logging
We provide a tool to log information. Default logging level is "INFO", you can call `logger.set_level(logging.DEBUG)` to change it.

> Please make sure you update to the `latest` version to use this feature.
```python
from spirit_gpu import start, logger
from spirit_gpu.env import Env
from typing import Dict, Any


def handler(request: Dict[str, Any], env: Env):
    """
    request: Dict[str, Any], from client http request body.
    request["input"]: Required.
    request["webhook"]: Optional string for asynchronous requests.

    we will only add request["meta"]["requestID"] if it not exist in your request.
    """
    request_id = request["meta"]["requestID"]
    logger.info("start to handle", request_id = request_id, caller=True)
    return {"output": "hello"}

start({"handler": handler})
```

## API
Please read [API](https://github.com/datastone-spirit/spirit-gpu/blob/main/API.md) or [中文 API](https://github.com/datastone-spirit/spirit-gpu/blob/main/API.zh.md) for how to use spirit-gpu serverless apis and some other import policies.

## Builder

The `spirit-gpu-builder` allows you to quickly generate templates and skeleton code for `spirit-gpu` using OpenAPI or JSON schema definitions. Built on `datamodel-code-generator`, this tool simplifies the setup for serverless functions.

> `spirit-gpu-builder` is installed when you install `spirit-gpu >= 0.0.6`.

```
usage: spirit-gpu-builder [-h] [-i INPUT_FILE]
                          [--input-type {auto,openapi,jsonschema,json,yaml,dict,csv,graphql}]
                          [-o OUTPUT_DIR]
                          [--data-type {pydantic_v2.BaseModel,dataclasses.dataclass}]
                          [--handler-type {sync,async,sync_generator,async_generator}]
                          [--model-only]

Generate spirit-gpu skeleton code from a OpenAPI or JSON schema, built on top of `datamodel-code-generator`. 
```

Options:
- `-h, --help`: show this help message and exit
- `-i INPUT_FILE, --input-file INPUT_FILE` Path to the input file. Supported types: ['auto', 'openapi', 'jsonschema', 'json', 'yaml', 'dict', 'csv', 'graphql']. If not provided, will try to find default file in current directory, default files ['api.yaml', 'api.yml', 'api.json'].
- `--input-type {auto,openapi,jsonschema,json,yaml,dict,csv,graphql}`: Specific the type of input file. Default: 'auto'.
- `-o OUTPUT_DIR, --output-dir OUTPUT_DIR`: Path to the output Python file. Default is current directory.
- `--data-type {pydantic_v2.BaseModel,dataclasses.dataclass}` Type of data model to generate. Default is 'pydantic_v2.BaseModel'.
- `--handler-type {sync,async,sync_generator,async_generator}` Type of handler to generate. Default is 'sync'.
- `--model-only`: Only generate the model file and skip the template repo and main file generation. Useful when update the api file.

The input file is the `input` part of body of your request to serverless of spirit-gpu, it can be json format, json schema format or openapi file.

**Examples**

The input file should define the expected `input` part request body for your serverless spirit-gpu function. Supported formats include JSON, JSON schema, or OpenAPI.

```yaml
openapi: 3.1.0·
components:
  schemas:
    RequestInput:
      type: object
      required:
        - audio
      properties:
        audio:
          type: string
          description: URL to the audio file.
          nullable: false
        model:
          type: string
          description: Identifier for the model to be used.
          default: null
          nullable: true
```

Your request body to `spirit-gpu`:

```json
{
    "input": {
        "audio": "http://your-audio.wav",
        "model": "base",
    },
    "webhook": "xxx"
}
```

Generated python model file:
```python
class RequestInput(BaseModel):
    audio: str = Field(..., description='URL to the audio file.')
    model: Optional[str] = Field(
        None, description='Identifier for the model to be used.'
    )
```

If using OpenAPI, ensure the main object in your YAML file is named RequestInput to allow automatic code generation.

```python
def get_request_input(request: Dict[str, Any]) -> RequestInput:
    return RequestInput(**request["input"])

def handler_impl(request_input: RequestInput, request: Dict[str, Any], env: Env):
    """
    Your handler implementation goes here.
    """
    pass

def handler(request: Dict[str, Any], env: Env):
    request_input = get_request_input(request)
    return handler_impl(request_input, request, env)
```



All generated code like this.
```
├── Dockerfile
├── LICENSE
├── README.md
├── api.json
├── requirements.txt
├── scripts
│   ├── build.sh
│   └── start.sh
└── src
    ├── build.py
    ├── main.py
    └── spirit_generated_model.py
```