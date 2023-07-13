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
    ```
    git clone https://github.com/OneHandedPirate/WebtronicsTask.git
    cd WebtronicsTask
    ```
2) If you use poetry:
   + install dependencies:
     ```
     poetry install
     ```
   + enter the poetry venv:
     ```
     poetry shell
     ```
   overwise:
   + Set up a new virtual environment, for example:
     ```
     virtualenv venv .
     ```   
   + Activate it:
     ```
     source venv/bin/activate
     ```   
   + Install dependencies:
     ```
     pip install -r requirements.txt
     ``` 
3) It the root directory of the project create `.env` file with the following set of variables:
    POSTGRES_USER - postgres user<br>
    POSTGRES_PASSWORD - postgres password<br>
    POSTGRES_DB - postgres database<br>
    POSTGRES_PORT - postgres port<br>
    POSTGRES_HOST postgres host<br>
    REDIS_HOST - redis host<br>
    REDIS_PORT - redis port<br>
    REDIS_DB - redis database<br>
    SECRET_KEY - secret key (used for creation and verification JWT tokens)<br>
    JWT_EXPIRATION_TIME - JWT token expiration time (in minutes)<br>
    POSTS_PER_PAGE - int value used for pagination 
    * If you don't plan to use real database and redis server and use docker I suggest using the following values in `.env`:<br>
        POSTGRES_USER - postgres<br>
        POSTGRES_PASSWORD - postgres<br>
        POSTGRES_DB - postgres<br>
        POSTGRES_PORT - any free port on your local machine<br>
        POSTGRES_HOST - localhost<br>
        REDIS_HOST - localhost<br>
        REDIS_PORT - any free port on your local machine<br>
        Then you can bring up docker-compose stack with postgres (with mounted volume to store data) and redis containers by a simple command:
        ```
        make up
        ```
4) Run migrations with alembic:
   ```
   alembic upgrade heads
   ```
   It will create all the table in database.
5) Run uvicorn server:
   ```
   uvicorn app.main:app
   ```

### Endpoints description:
`/login`, method=POST - login for the registered users with email and password.<br>
`/user`, method=POST - create a new user with email and password (registration).<br>
`/user/{uuid}`, method=GET - get the user with the specified uuid.<br>
`/posts`, method=POST - create a new post with the specified `title`, `content` and `published` (optional) values. Only for authorized users.<br>
`/posts`, method=GET - get first ${POST_PER_PAGE} posts from db with the `published` set to true. Optional query parameter for `page` for pagination.<br>
`/posts/{post_id}`, method=GET - get the specified post if it is `published`.<br>
`/posts/{post_id}`, method=PUT - update the specified post. Only for its author. Since PUT is for updating all fields, all 3 values (`title`, `content` and `published`) should be provided.<br>
`/posts/{post_id}`, method=DELETE - delete the specified post. Only for its author.<br>
`/posts/vote`, method=POST - vote for the specified. Provided boolean value `is_like` defines whether it is a like (True) or dislike (False). Then there is some ugly redis magic to update the cashed value of result rating (likes - dislikes) and create or update Vote table entry, describing performed action. 

### Notes:
* "Rating" field calculation in post response (whether it is an individual post or list of them) is rather tricky. First it looks up at redis for specific key (vote:{post_id}:result), if there is no such key then it looks up for all the entries in Vote table with the post_id. If there are no such entries - the redis value of vote:{post_id}:result is set to 0, otherwise it is calculated from those entries and all the Vote entries for the post is duplicated to redis (that is needed for like/dislike functionality to work correctly).
* I couldn't get the hunter.io API key since the validation there is something. But it seems to that the function for email verification could look like this:
    ```
    async def verify_email(email: string):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.hunter.io/v2/email-verifier?email={email}&api_key=API_KEY")
            data = response.json()
            if not data["data"]["status"] == "valid":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalide email")
    ``` 
