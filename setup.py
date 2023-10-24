from setuptools import find_packages, setup

setup(
    name = 'chat-therapy',
    version = '0.1',
    description = 'microservice backbone for conversational chatbot agents with therapeutic capacities',
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    author = 'Mohamad Amin Katebsaber',
    author_email = 'katebsaber96@gmail.com',
    maintainer = 'Mohamad Amin Katebsaber',
    maintainer_email = 'katebsaber96@gmail.com',
)