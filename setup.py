from distutils.core import setup
from libfurc import __version__ as version

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
    packages=["libfurc"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers", 
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: zlib/libpng License",
        "Topic :: Software Development :: Libraries"
    ]
)
