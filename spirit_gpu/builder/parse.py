import argparse
import dataclasses
from enum import Enum
import os
from datamodel_code_generator import InputFileType, DataModelType


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
    model_only: bool = False

    def check(self):
        cwd = os.getcwd()
        default_files = ["api.yaml", "api.yml", "api.json"]
        if not self.input_file:
            for file in default_files:
                if os.path.exists(os.path.join(cwd, file)):
                    print(f"Using default input file: {file}")
                    self.input_file = file
                    break
            if not self.input_file:
                raise ValueError(
                    f"Input file is not provided and no default file found. Supported default files: {default_files}"
                )
        if not self.output_dir:
            self.output_dir = cwd


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
        required=False,
        default="",
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
        "-o",
        "--output-dir",
        required=False,
        default="",
        help="Path to the output Python file.",
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

    parser.add_argument(
        "--model-only",
        required=False,
        action="store_true",
        help="Generate the model file only when you update the model config",
    )

    args = parser.parse_args()
    arguments = Arguments(
        input_file=args.input_file,
        input_type=InputFileType(args.input_type),
        output_dir=args.output_dir,
        data_type=DataModelType(args.data_type),
        handler_type=HandlerType(args.handler_type),
        model_only=args.model_only,
    )
    arguments.check()
    print("Building spirit-gpu skeleton code with following arguments:")
    for k, v in dataclasses.asdict(arguments).items():
        print(f"\t{k}: {v}")
    print()
    return arguments
