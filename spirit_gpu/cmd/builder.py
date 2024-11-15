from ..builder import parse
from ..builder import generator


def main():
    args = parse.get_args()
    if args.model_only:
        generator.generate_model_file(args)
        return
    generator.generate_template_repo(args)
    generator.generate_model_file(args)
    generator.generate_main_file(args)
    print("All files generated")


if __name__ == "__main__":
    main()
