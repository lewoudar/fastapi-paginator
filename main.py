from fastapi import FastAPI
from pydantic import BaseModel, Field

# import all you need from fastapi-pagination
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.ext.sqlalchemy_future import paginate

app = FastAPI()  # create FastAPI app


class UserOut(BaseModel):  # define your model
    name: str = Field(..., example="Steve")
    surname: str = Field(..., example="Rogers")


users = [  # create some data
    # ...
]


@app.get('/users', response_model=Page[UserOut])  # use Page[UserOut] as response model
async def get_users():
    return paginate(users)  # use paginate function to paginate your data


add_pagination(app)  # important! add pagination to your app