from setuptools import setup

setup(
    name="neon-dungeon",
    version="1.0.0",
    py_modules=["neon_dungeon"],
    entry_points={
        "console_scripts": [
            "neon-dungeon=neon_dungeon:run_cli",
        ],
    },
    install_requires=[],
    author="Jules",
    description="An offline Python terminal roguelite game.",
    python_requires=">=3.6",
)
