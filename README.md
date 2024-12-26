# intl-docs-chatbot
Chatbot for intl docs

# Steps to run the chatbot using Docker

1. Clone the repository
2. Run the following command to build the docker image
```
docker build -t chatbot .
```
3. Run the following command to run the docker container
```
docker run --name chatbot-container chatbot
```
4. Command to stop the container
```
docker stop chatbot-container
```
5. Command to remove the container
```
docker rm chatbot-container
```