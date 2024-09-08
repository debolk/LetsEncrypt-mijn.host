from setuptools import setup

setup(
    name='certbot-dns-mijnhost',
    package='dns_mijnhost.py',
    version='1.1.0',
    author="Melody Smit",
    url="https://github.com/debolk/LetsEncrypt-mijn.host",
    install_requires=[
        'certbot',
    ],
    entry_points={
        'certbot.plugins': [
            'dns-mijnhost = dns_mijnhost:Authenticator',
        ],
    },
)
