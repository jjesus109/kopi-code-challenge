# Kopi code challenge

## Design

The solution was designed following this C4 model.

![C4 Model](docs/images/c4-model.png?raw=true)

and using this data model

![C4 Model](docs/images/data-model.png?raw=true)

### Main layer

The App was created following a clean architecture, made by 4 different layers:

- Entities: Here lives the data structures used to comunicate between all the layers
- Drivers: Here are all the  connections to external resources as database and connection to LLM
- Adapters: Is the bridge with drivers that help us to manage all the drivers and add the logic to accomplish business needs
- Cases: Here lives the business logic, using the adapters will help to achive the business needs.

### Proxy Component
Also the app has a proxy component that helps to validate if the user input or LLM response are valid, valid means that doesn't contains and attack to the LLM. The categories covered are:

- Prompt Injection.
- Insecure Output Handling
- Model Denial of Service
- Insecure Plugin Design
- Excessive Agency
- Sensitive Info Disclosure

This component its divided in 3 layers:

- Proxy: Has the main logic to know what to do with the results given by the policy
- Policy: Process the messages received and determine if the message is valid or not
- Drivers: Manage all the external connections to the agent and the mocked external system that notifies when a message wants to reveal sensitive data or change made something different from the original instructions


### Extras
Also th project have other files as:

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

`make restart`: Restart the services and show the live logs of the containers

`make logs`: Show the logs of the running containers

`make clean`: teardown and removal of all containers