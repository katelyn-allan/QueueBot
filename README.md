# QueueBot

Configures a discord bot that can be used to organize users into games of Heroes of the Storm through allowing them to assign roles that will be prioritized, then sorting them into two teams of 5, which will be balanced by an internally tracked MMR.

## First-time Setup
Create a copy of `env_template.txt`, rename it to `.env` and populate with your equivalent values for your server and application.

If you do not have a database setup to use, create a file in this directory called `player_data.db`. In the `.env` file, under `DB_PATH`, put `./player_data.db`

#### Using Docker
_(Please note that running the application through docker requires the database file to be local to the docker environment at this time)._
This application allows running through docker. Docker desktop can be installed [here](https://www.docker.com/products/docker-desktop/).

To run using docker, navigate to the folder the code is installed in in your terminal and run `docker compose up`.

You should see the project running in docker desktop and can monitor its outputs there!

#### Using Python
This project is built on Python 3.11.0, and uses pip-tools to manage dependencies. It is recommended to use a virtual environment to manage the dependencies.
Run `pip install -r requirements.txt` to install the required packages.

You can run the bot with `python core.py` or `python3 core.py` depending on your system.

## Package Management (pip-tools)
This project uses pip-tools to manage dependencies. To add a new dependency, add it to `requirements.in` and run `pip-compile requirements.in` to generate a new `requirements.txt` file. This will also update the `requirements.txt` file to the latest versions of all packages that are codependency resolved.

Optionally, you can use `pip-compile --upgrade requirements.in` to only upgrade the packages that are already in the `requirements.txt` file.
Or `pip-compile --resolve=backtracking requirements.in` to use a slower, but more accurate dependency resolver.

## Pre-commit Styling and Code Style
This project uses pre-commit to run a series of checks on the code before allowing merging to the main branch. A github action is in place to block PR merging unless the pre-commit checks pass.
To run pre-commit locally, run `pre-commit run --all-files` in the root directory of the project.

This will run the 'Ruff' sweet of linters, and then the 'Black' code formatter. Several checks in both of these libraries will auto fix issues, but some will require manual fixing.

A list of relevant Ruff flags, and a link to documentation, as well as configuration of Ruff can be found in the `pyproject.toml` file.

In certain cases, Ruff needs to be ignored for code functionality (a common example is it flagging long strings which cannot be multi-line strings due to formatting with 'line too long'), in these cases, append # noqa: IssueNumber to the end of the line to ignore the issue.

example:
```python
my_string = "This is a very long string that cannot be multi-line" # noqa: E501
```

This project uses Google convention for docstrings.