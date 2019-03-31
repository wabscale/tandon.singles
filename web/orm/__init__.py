from web.orm.Sql import Sql, Table, JoinedTable
from web.orm.BaseModel import BaseModel, TempModel
from web.orm.Query import Query
from web.orm.utils import utils


if __name__ == "__main__":
    print(Sql.SELECTFROM('Person').WHERE(username='admin').do())
