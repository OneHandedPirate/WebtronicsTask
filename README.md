<h1 align="center">Test Task</h1>

### Task:

	Create a simple RESTful API using FastAPI for a social networking application
    Functional requirements:
    - There should be some form of authentication and registration (JWT, Oauth, Oauth 2.0, etc..)
    - As a user I need to be able to signup and login
    - As a user I need to be able to create, edit, delete and view posts
    - As a user I can like or dislike other users’ posts but not my own 
    - The API needs a UI Documentation (Swagger/ReDoc)

    Bonus section (not required):
    - Use https://clearbit.com/platform/enrichment for getting additional data for the user on signup
    - Use emailhunter.co for verifying email existence on registration
    - Use an in-memory DB for storing post likes and dislikes (As a cache, that gets updated whenever new likes and dislikes get added) 

<hr>
    

### Prerequisites:
- docker, docker-compose installed<br> 
    or
- postgresql and redis server up and running

### Installation

1) Clone the repo and cd into its directory:
    