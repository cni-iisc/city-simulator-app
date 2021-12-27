# City Simulator: City-scale agent-based epidemic simulator as service


## Setting up
The interface is developed using Django (a python framework) and has been tested and is known to work in Linux/ Unix distributions. Due to some packages that is used for example `Celery` (which is used as the task queue), the interface does not support deployment on Windows machines natively. In windows, you will be able to run the soure code in Windows Subsystem for Linux (WSL) environments.

Software dependencies:
 - [Python 3.8+](https://www.python.org/downloads/)
 - [Python-venv](https://docs.python.org/3/library/venv.html) (for creating virtual environments, check if an install is required)
 - [Rabbitmq-server](https://www.rabbitmq.com/download.html)
 - CPP (for simulator)
 - GNUPlot (for simulator)
 - git (for simulator)
 - make (for simulator)

The python packages required for running the interface is listed in `requirements.txt`.

> **NOTE:** This is a code release and the database configurations are currently the default, sqlite3 database. You may want to configure the database based on your requirements, more information on database configurations are available in [the official documentation of Django for databases](https://docs.djangoproject.com/en/3.2/ref/settings/#databases).

> **NOTE**: These steps are for the interface is alone, in the next release, we shall package the setup through a makefile to make it easy for setting both the application interface and the agent-based simulator.

The next step will be to create a virtual environment, this is optional but is recommended. You can also you Anaconda or virtualenv for this step, but we use the built-in `venv` tool to create and activate a virtual environment called `env`.

```shell
$ python3 -m venv env
$ source ./env/bin/activate
```
Once the virtual environment is active, the name of the virtual environment appears at the start of the prompt as follows,
```shell
(env) $
```

Now, we install the required python packages with the following command,
```shell
(env) $ pip install -r requirements.txt
```
Before going to the next step, let us fetch the code and build the executable for the agent-based simulator. The agent-based simulator is already linked as a git submodule and can the executable can be built by running the following commands:

```shell
(env) $ git submodule update --init
(env) $ git submodule update --remote
(env) $ cd simulator/cpp-simulator
(env) $ make -f Makefile_np all
```
> Note: On the production environment, do run the command 
> ```shell
>(env) $ python manage.py collectstatic
>```
> 
The next step is to set-up the database schema and saving the schema to the database. This is done using the following sequence of commands:
```shell
(env) $ python manage.py makemigrations
(env) $ python manage.py migrate
```
The last step before running the interface is to create a superuser, who has an admin panel to have more privileges on working with the database. We use the default admin interface provided in Django, and [more information is available in this documentation](https://docs.djangoproject.com/en/3.2/ref/contrib/admin/). The command to create the superuser is,
```shell
(env) $ python manage.py createsuperuser
```
This will be an interactive command-line prompt, where the **username** is the **email address of the admin** with a password.
Now, the setup is complete and we are ready to start City Simulator.

## Starting City Simulator
City Simulator, runs as two services, which are opened in two separate screens (while starting City Simulator on servers, `tmux` or `screen` can be considered to multiplex the terminal window).

The first service is the application server, which provides the user-interface and also contains the configurations for running the agent-based simulator, and is run using:
```shell
(env) $ python manage.py runserver
```
The second service is the task queue to manage running background tasks like the instantiation of a synthetic city, the simulations, sending emails (if configured), and is run using the following command:
```shell
(env) $ celery -A config worker -l INFO -Q mailQueue,instQueue,simQueue
```

## License
The source code for this application is shared under the usage of terms of the Apache2 License. The copyright is owned by the Centre for Networked Intelligence at the Indian Institute of Science, Bangalore

