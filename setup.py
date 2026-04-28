"""Setup configuration for envault package."""

from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="envault",
    version="0.1.0",
    description="Lightweight secrets manager that encrypts .env files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="envault contributors",
    python_requires=">=3.8",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "cryptography>=41.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov",
        ]
    },
    entry_points={
        "console_scripts": [
            "envault=envault.cli:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Security :: Cryptography",
        "Topic :: Utilities",
    ],
    project_urls={
        "Source": "https://github.com/your-org/envault",
        "Bug Tracker": "https://github.com/your-org/envault/issues",
    },
)
