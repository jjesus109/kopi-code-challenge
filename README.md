# Kopi code challenge

## Design

The solution was designed following this C4 model.

![C4 Model](docs/images/c4-model.png?raw=true)

and using this data model

![C4 Model](docs/images/data-model.png?raw=true)

The App was created following a clean architecture, made by 4 different layers

- Entities: Here lives the data structures used to comunicate between all the layers
- Drivers: Here are all the  connections to external resources as database and connection to LLM
- Adapters: Is the bridge with drivers that help us to manage all the drivers and add the logic to accomplish business needs
- Cases: Here lives the business logic, using the adapters will help to achive the business needs.

Also we have some other files as:

- errors: Where all custom errors are created to manage some possible scenarios in the flows
- models: Where the request models lives 
- configuration: A file that contains all the enviroment variable that help us to configure our app
- db: the configuration of the database connection
- depends: Here are the creation of all the layers and the dependency injection of all.
- utils: Some additional tools used in the app. ex: logging configuration


## Commands tool

If you want to run in your local machine you can do it following the next commands:

`make`: shows a list of all possible make commands

`make install`: install all requirements to run 
the service. if some tool is required for the installation, you must detect its absence and provide installation instructions

`make test`: run tests

`make run`: run the service and all related services (such as a db) in Docker

`make down`: teardown of all running services

`make clean`: teardown and removal of all containers