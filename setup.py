from setuptools import setup

version = "0.1.0"

long_description = None
with open("readme.md", "r") as f:
    long_description = f.read()

setup(
    name="libfurc",
    version=version,
    description="A library for handling Furcadia things.",
    long_description=long_description,
    long_description_content_type="text/markdown" if long_description else None,
    url="https://github.com/FelixWolf/libFurc",
    author="Félix",
    author_email="felix.wolfz@gmail.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers", 
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries"
    ]
)
