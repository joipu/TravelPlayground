# Set up venv in Debian system.
```
sudo apt-get install python3-venv
```

# Set up virtual venv

```
python3 -m venv venv
source venv/bin/activate # for bash only. Use `source venv/bin/activate.fish` for fish.
pip3 install -r requirements.txt
```
On a new server, it's possible the firewall doesn't allow incoming request. Allow requests on the port:
```
sudo ufw allow 6003/tcp
```

# Start the website backend service

1. Assuming fish shell, enable the python virtual environment:

```
source venv/bin/activate.fish
```

If using bash, use
```
source venv/bin/activate
```

2. Start the backend service

```
python src/app.py
```

# Set up the CLI service

1. In VS Code, open this project. Create `.env` file with and add

```
TRAVEL_PLAYGROUND_OPENAI_API_KEY='<key>'.
```

2. Use `cmd + shift + p` and select "Python: Create Environment". Choose `Venv`, and select "requirements.txt" to install deps. Wait for it to finish.
3. Open terminal in VS Code, you should see `(.venv)` at the beginning of your terminal prompt. Also make sure the terminal working directory is at top level folder of this repository (where setup.py is located)
4. Run `pip install -e .`
5. After that, you should be able to run `food_finder "sushi in tokyo"` to execute the code.
6. Any new changes should be automatically picked up when you execute this command again.


# Set up and Use Redis locally
1. First, install Redis on your machine: `brew install redis`
2. Install the Redis Python client: `pip3 install redis`
3. Spin up the Redis server (local): `redis-server`. By default, it should run at port 6379.
4. Open a new command and run `redis-cli`
5. To authenticate (if required): `AUTH your_password`  

### Common queries to check caches on Redis:
* `KEYS *`: List all the keys in cache
* `KEYS tabelog:restaurant:*`
* `KEYS tabelog:restaurant:<ikyu_id>`, e.g. `EXISTS tabelog:restaurant:109656`: Check if a specific key exists
* `GET tabelog:restaurant:109656`: Get the value of a key
* `TTL tabelog:restaurant:109656`: Check the TTL of a key
* `DEL tabelog:restaurant:109656`: Delete a key
