from setuptools import setup

setup(
    name='certbot-dns-mijnhost',
    package='dns_mijnhost.py',
    install_requires=[
        'certbot',
    ],
    entry_points={
        'certbot.plugins': [
            'dns-mijnhost = dns_mijnhost:Authenticator',
        ],
    },
)
