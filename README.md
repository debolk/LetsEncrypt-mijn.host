To work on this plugin:

```
git clone https://github.com/certbot/certbot
sudo apt update
sudo apt install python3-venv libaugeas0
```


If using ArchLinux, use this instead of apt:
```
sudo pacman -S python3-venv augeas
```

After installing run this to create a virtual environment:
```
cd certbot
python tools/venv.py
. venv/bin/activate (for activating virtual environment)
```
And point IDE (if applicable) to certbot/venv/bin/python3.12

------------------------------------------
To test plugin in certbot dev environment:

```
. certbot/venv/bin/activate
pip install -e dns_mijnhost/
certbot_test plugins
```

Dry-run test command:
```
certbot certonly -a dns-mijnhost --dns-mijnhost-api_key <API_KEY> -d bolkhuis.nl --dry-run --config-dir test/config --work-dir test/work --logs-dir test/logs
```
