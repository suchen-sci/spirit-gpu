import argparse
import dataclasses
from enum import Enum
from datamodel_code_generator import InputFileType, DataModelType
import pprint


class HandlerType(Enum):
    Sync = "sync"
    Async = "async"
    SyncGenerator = "sync_generator"
    AsyncGenerator = "async_generator"


@dataclasses.dataclass
class Arguments:
    input_file: str
    input_type: InputFileType
    output_dir: str
    data_type: DataModelType
    handler_type: HandlerType


def get_args():
    parser = argparse.ArgumentParser(
        description=(
            "Generate spirit-gpu skeleton code from a OpenAPI or JSON schema, built on top of datamodel-code-generator."
            "Please check more details about usage of generated code from https://github.com/datastone-spirit/spirit-gpu"
        )
    )

    input_types = [t.value for t in InputFileType]
    parser.add_argument(
        "-i",
        "--input-file",
        required=True,
        help=f"Path to the input file. Supported types: {input_types}.",
    )
    parser.add_argument(
        "--input-type",
        required=False,
        default="auto",
        choices=input_types,
        help=f"Specific the type of input file. Default: 'auto'.",
    )

    data_types = [
        DataModelType.PydanticV2BaseModel.value,
        DataModelType.DataclassesDataclass.value,
    ]
    parser.add_argument(
        "-o", "--output-dir", required=True, help="Path to the output Python file."
    )
    parser.add_argument(
        "--data-type",
        required=False,
        choices=data_types,
        default="pydantic_v2.BaseModel",
        help="Type of data model to generate. Default is 'pydantic_v2.BaseModel'.",
    )

    handler_types = [t.value for t in HandlerType]
    parser.add_argument(
        "--handler-type",
        required=False,
        default=HandlerType.Sync.value,
        choices=handler_types,
        help=f"Type of handler to generate. Default is 'sync'.",
    )

    args = parser.parse_args()
    arguments = Arguments(
        input_file=args.input_file,
        input_type=InputFileType(args.input_type),
        output_dir=args.output_dir,
        data_type=DataModelType(args.data_type),
        handler_type=HandlerType(args.handler_type),
    )
    print("Building spirit-gpu skeleton code with following arguments:")
    pprint.pprint(arguments)
    return arguments
