from setuptools import setup, find_packages

requires = [
    'python-telegram-bot',
    'pyyaml',
    'pytesseract',
    'pdf2image'
]

setup(
    name='atexter_bot',
    version='0.1',
    description='telegram bot to extract text from pdf files',
    classifiers=[
        'Programming Language :: Python',
    ],
    author='atronah',
    author_email='atronah.ds@gmail.com',
    keywords='python telegram bot google tesseract ocr',
    packages=find_packages(),
    install_requires=requires,
)