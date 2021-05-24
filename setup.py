import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="electiondata",
    version="1.5.4",
    author="Kavi Gupta",
    author_email="electiondata@kavigupta.org",
    description="Set of APIs and scripts for normalizing election data.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kavigupta/electiondata",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "attrs>=21.2.0",
        "requests>=2.25.1",
        "pandas>=1.2.4",
        "permacache>=2.0.2",
        "addfips==0.3.1",
        "fuzzy-match==0.0.1",
        "openpyxl>=3.0.7",
        "us>=2.0.2",
        "lxml==4.6.3",
    ],
)
