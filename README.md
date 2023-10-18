# Set up project.

1. In VS Code, open this project. Create `.env` file with and add

```
TRAVEL_PLAYGROUND_OPENAI_API_KEY='<key>'.
```

2. Use `cmd + shift + p` and select "Python: Create Environment". Choose `Venv`, and select "requirements.txt" to install deps. Wait for it to finish.
3. Open terminal in VS Code, you should see `(.venv)` at the beginning of your terminal prompt. Also make sure the terminal working directory is at top level folder of this repository (where setup.py is located)
4. Run `pip install -e .`
5. After that, you should be able to run `food_finder "sushi in tokyo"` to execute the code.
6. Any new changes should be automatically picked up when you execute this command again.
