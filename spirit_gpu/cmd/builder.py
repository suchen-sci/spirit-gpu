import builder.parse as parse
import builder.generator as generator


def main():
    args = parse.get_args()
    generator.generate_template_repo(args)
    generator.generate_model_file(args)
    generator.generate_main_file(args)

if __name__ == "__main__":
    main()
