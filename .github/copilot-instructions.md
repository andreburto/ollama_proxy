# Ollama Proxy Instructions

## Description

This project contains instructions for using the Ollama Proxy, which is a tool designed to facilitate communication between clients and the Ollama API. The instructions cover various aspects of setting up and using the proxy effectively.

This project is structured into three main parts: the Proxy, the Worker, and the Frontend. Each part has specific responsibilities and functionalities that contribute to the overall operation of the Ollama Proxy. The project is designed to handle the slow response times of the Ollama API by implementing a queuing system and providing a user-friendly interface for clients to interact with the API.

The language to use for the proxy and worker is Python. The fontend will be vanilla JavaScript, HTML, and CSS. The proxy will use the Flask framework to handle HTTP requests and responses, while the worker will be responsible for processing the queued prompts and communicating with the Ollama API. The frontend will provide a simple and intuitive interface for users to submit prompts and view results.

The queue will be implemented using SQLite. It will contain a table to store the prompts, their statuses, and the results once they are processed. The worker will continuously check the queue for new prompts, process them by sending requests to the Ollama API, and update the status and results in the database accordingly. The three states for the prompts will be "queued", "processing", and "completed". This will allow clients to track the progress of their prompts and retrieve results once they are available.

## Parts

### Proxy

The proxy is a server that acts as an intermediary between clients and the Ollama API. It handles requests from clients, forwards them to the Ollama API, and returns the responses back to the clients. Because Ollama can be slow to respond, the proxy will have four endpoints:


#### Static Serving
1. `/`: This endpoint will serve the frontend of the application, which will allow users to interact with the proxy through a web interface.
2. `/list`: This endpoint will serve a page that lists all the prompts in the queue along with their statuses. This will allow users to see the overall state of the queue and track multiple prompts at once. It will return an HTML page that displays the unique IDs, statuses, and timestamps for each prompt in the queue in a table format. This page will be designed to be user-friendly and easy to navigate, allowing users to quickly find the information they need about their prompts. The page will also include pagination controls to handle large numbers of prompts efficiently, allowing users to navigate through different pages of the queue as needed.

#### API Endpoints
1. `/api/v1/prompt`: This endpoint will accept prompts in the form of JSON post requests. The proxy put these prompts in a queue and return a unique ID for each prompt.
2. `/api/v1/prompt/:id/status`: This endpoint will allow clients to check the status of their prompts using the unique ID returned from the first endpoint. It will return whether the prompt is still in the queue, being processed, or has been completed.
3. `/api/v1/prompt/:id/result`: This endpoint will allow clients to retrieve the result of their prompts once they have been processed. It will return the response from the Ollama API.
4. `/api/v1/prompts`: This endpoint will return a list of all prompts in the queue along with their statuses. This will allow clients to see the overall state of the queue and track multiple prompts at once. It will return a JSON array containing the unique IDs, statuses, and timestamps for each prompt in the queue. This end point is a GET request. Implement pagination for this endpoint to handle large numbers of prompts efficiently. Clients can specify the page number and page size through query parameters to retrieve a subset of the prompts in the queue. Default to a 5 prompts per page if no parameters are provided. Start with the newest prompts first, so the prompts should be ordered by timestamp in descending order by creation time.


The web server for the proxy will use the standard library `http.server` module to serve the frontend and handle API requests. The proxy will also use the `sqlite3` module to manage the queue and store prompt data in a SQLite database. The unique IDs for each prompt will use the `uuid` module to generate unique identifiers. The proxy will be designed to handle multiple concurrent requests and ensure that the queuing system works efficiently to manage the slow response times of the Ollama API.

Use port 8000 for the proxy server to listen for incoming requests. The proxy will be responsible for managing the queue and ensuring that prompts are processed in a timely manner, while also providing a responsive interface for clients to interact with the Ollama API. Allow access from any origin to the proxy server to enable clients from different domains to interact with the API without facing cross-origin issues.

### Worker

The worker is responsible for processing the queued prompts. It continuously checks the queue for new prompts, sends requests to the Ollama API, and updates the status and results in the database.

The worker will run in a separate process from the proxy to ensure that the proxy can continue to accept new prompts while the worker is processing existing ones. The worker will use the unique IDs from the queue to track which prompts it is processing and update their statuses accordingly. When a prompt is completed, the worker will update the status to "completed" and store the result in the database, making it available for retrieval through the proxy's endpoints.

The worker will use the Ollama API to process the prompts. It will send requests to the API and handle the responses, ensuring that the results are stored correctly in the database for retrieval by clients.

The only model to use for the worker is "llama3.2". This will ensure that all prompts are processed using the same model, providing consistency in the results returned to clients. Disable caching in the worker to ensure that each prompt is processed fresh and that clients receive the most up-to-date results from the Ollama API.

### Frontend

All pages should be a single file with minimal CSS, no external dependencies, and use vanilla JavaScript for interactivity. The interface will include a form for submitting prompts, a section for displaying the status of submitted prompts, and a section for displaying the results once they are available.

Each page will have a menu on the top left that links to all the pages below:
* `/` - Home
* `/list` - All Prompts

#### `/`
The frontend will be a simple web interface that allows users to submit prompts and view results. It will communicate with the proxy through the defined endpoints to submit prompts, check their status, and retrieve results. The frontend will be designed to provide a user-friendly experience, making it easy for users to interact with the Ollama API through the proxy.

The workflow for the frontend will be as follows:
1. The user submits a prompt through the form.
2. The frontend sends a POST request to the `/api/v1/prompt` endpoint with the prompt data.
3. The frontend receives a unique ID for the prompt and starts polling the `/api/v1/prompt/:id/status` endpoint to check the status of the prompt.
4. Once the status indicates that the prompt has been completed, the frontend sends a GET request to the `/api/v1/prompt/:id/result` endpoint to retrieve the result.
5. The frontend displays the result to the user in a readable format.

#### `/list`
The `/list` page will provide a comprehensive view of all prompts in the queue, allowing users to track the status of their prompts and see the overall state of the queue. This page will display a table with the unique IDs, statuses, and timestamps for each prompt in the queue. Users will be able to easily navigate through the list of prompts and see the progress of their submissions. The page will also include pagination controls to handle large numbers of prompts efficiently, allowing users to navigate through different pages of the queue as needed. This will ensure that users can easily find the information they need about their prompts without being overwhelmed by a long list of entries. The design will be clean and straightforward, making it easy for users to understand the status of their prompts at a glance.

The workflow for the frontend will be as follows:
1. The user navigates to the `/list` page.
2. The frontend sends a GET request to the `/api/v1/prompts` endpoint to retrieve the list of prompts in the queue.
3. The frontend receives a JSON array containing the unique IDs, statuses, and timestamps for each prompt in the queue.
4. The frontend displays the prompts in a table format, allowing users to easily see the status of their prompts and track their progress.
5. The frontend includes pagination controls to allow users to navigate through different pages of the queue if there are many prompts. This will ensure that the interface remains user-friendly and efficient, even as the number of prompts in the queue grows.