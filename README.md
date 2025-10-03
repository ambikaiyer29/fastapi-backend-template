
### Project Structure

* **/app**: The main container for our application code.
* **/api/v1**: This will house our API version 1, with endpoints.py defining the routes.
* **/core**: This module will contain the core logic of our application, such as configuration, logging setup, and metrics instrumentation.
* **/utils**: A place for utility functions and decorators that can be reused across the application.
* **main.py**: The entry point of our FastAPI application.
* **requirements.txt**: This file will list all the project dependencies.


### Setup a Virtual environment

```commandline
 python3.11 -m venv .venv && source .venv/bin/activate  
```

Now install the dependencies:
```commandline
pip install -r requirements.txt
```

### Running the application

```commandline
uvicorn app.main:app --reload
```