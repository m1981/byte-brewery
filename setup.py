from setuptools import setup, find_packages

setup(
    name="augment_ai",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        # Add only runtime dependencies here
    ],
    extras_require={
        'dev': [
            'pytest',  # for testing
        ],
    },
    entry_points={
        'console_scripts': [
            'aug=augment_ai.aug_pipeline:main',
        ],
    },
)