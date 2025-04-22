from setuptools import setup, find_packages

setup(
    name="augment_ai",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "argparse",  # Add all runtime dependencies
    ],
    extras_require={
        'dev': [
            'pytest',
            'build',
            'twine',
            'wheel'
        ],
    },
    python_requires='>=3.6',  # Specify minimum Python version
    description="Augment AI utility tools",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/m1981/byte-brewery",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    entry_points={
        'console_scripts': [
            'aug=augment_ai.aug_pipeline:main',
        ],
    },
)