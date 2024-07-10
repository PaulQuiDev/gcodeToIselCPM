from setuptools import setup, find_packages

setup(
    name='gcodeToIselCPM',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'pillow==9.5.0',
        'numpy==1.24.3',
        'matplotlib==3.7.1',
        'pyserial==3.5',
        # ajoutez d'autres dépendances ici
    ],
    python_requires='~=3.11',
    url='https://github.com/PaulQuiDev/gcodeToIselCPM',
)