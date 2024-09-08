To work on this plugin:

```
git clone https://github.com/certbot/certbot
sudo apt update
sudo apt install python3-venv libaugeas0
    (sudo pacman -S python3-venv augeas for ArchLinux)

cd certbot
python tools/venv.py
. venv/bin/activate (for activating virtual environment)
```
And point IDE (if applicable) to certbot/venv/bin/python3.12

To test plugin in certbot dev environment:

```
. certbot/venv/bin/activate
pip install -e plugin/
certbot_test plugins
```
