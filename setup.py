"""
Set up the package.
"""

from setuptools import setup, find_packages


def load_requirements():
    with open("requirements.txt", encoding="UTF-8") as requirements:
        return requirements.read().splitlines()


extras_require = {
    "test": [
        "pytest",
    ]
}

if __name__ == "__main__":

    setup(
        name="sprite-gpu",
        use_scm_version=True,
        setup_requires=["setuptools>=45", "setuptools_scm", "wheel"],
        install_requires=load_requirements(),
        extras_require=extras_require,
        packages=find_packages(),
        python_requires=">=3.9",
        description="Python serverless framework for Datastone Sprite GPU.",
        long_description="For more details, please visit https://github.com/datastone-sprite/sprite-gpu",
        long_description_content_type="text/markdown",
        author="Sprite",
        author_email="pypi@datastone.cn",
        url="https://github.com/datastone-sprite",
        project_urls={
            "Documentation": "https://github.com/datastone-sprite/sprite-gpu/blob/main/README.md",
            "Source": "https://github.com/datastone-sprite/sprite-gpu",
            "Bug Tracker": "https://github.com/datastone-sprite/sprite-gpu/issues",
        },
        classifiers=[
            "Topic :: Software Development :: Libraries :: Application Frameworks",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3.9",
            "Operating System :: OS Independent",
            "Environment :: GPU",
        ],
        include_package_data=True,
        keywords=[
            "serverless",
            "ai",
            "gpu",
            "machine learning",
            "SDK",
            "library",
            "python",
            "API",
        ],
        license="MIT",
    )
