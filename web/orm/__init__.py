from web.orm.BaseModel import BaseModel, TempModel
from web.orm.Query import Query
from web.orm.Sql import Sql, Table, JoinedTable
from web.orm.types import Column, Integer, Text, Varchar, DateTime
from web.orm.utils import strptime, classproperty


class Test(BaseModel):
    test_name = Column(Varchar(128), primary_key=True, references='Person.username')


class bsql:
    query = Query

    def __init__(self):
        pass


if __name__ == "__main__":
    t = Test.query.find(test_name='abc').first()
    print(t)

    # p=Query(Photo).find(photoOwner='admin').all()
    # print(p)
    # Query('Person').new(username='admin')
    # Sql.SELECTFROM('Person').WHERE(username='admin').GROUPBY('lname').ORDERBY('username').first()
    # Query.create_all()
