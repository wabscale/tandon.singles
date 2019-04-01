from web.orm.Sql import Sql, Table, JoinedTable
from web.orm.BaseModel import BaseModel, TempModel
from web.orm.Query import Query
from web.orm.utils import utils


if __name__ == "__main__":
    from web.models import *
    p = Query('Person').find(username='admin').first()
    print(p)
    print('\n'.join( str(i) for i in list(p.photo)))

    # print(Sql.INSERT(username='admin').INTO('Person').do())
    # Query()
