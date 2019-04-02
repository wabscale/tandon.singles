from web.orm.Sql import Sql, Table, JoinedTable
from web.orm.BaseModel import BaseModel, TempModel
from web.orm.Types import Column, Integer, Text, Varchar, DateTime
from web.orm.Query import Query
from web.orm.utils import utils


# class Test(BaseModel):
#     test_name=Column(Varchar(128), primary_key=True, references='Person.username')

if __name__ == "__main__":
    # Query('Person').new(username='admin')
    Sql.SELECTFROM('Person').WHERE(username='admin').GROUPBY('lname').ORDERBY('username').first()
    Query.create_all()
