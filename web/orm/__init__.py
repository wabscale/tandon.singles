from web.orm.Sql import Sql, Table, JoinedTable
from web.orm.BaseModel import BaseModel, TempModel
from web.orm.Query import Query
from web.orm.utils import utils


if __name__ == "__main__":
    from web.models import *

    # admin=Query('Person').new(username='admin')
    p=Query('Person').find(username='admin').first()
    photo=Query('Photo').new(photoOwner='admin')

    print(p)

    print('\n' + '\n'.join(str(i) for i in list(p.photos)))
