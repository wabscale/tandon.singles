from . import Sql


class Query(object):
    def __init__(self, table):
        self.table = table

    def find(self, **conditions):
        """
        similar to sqlalchemy's Sql.filter_by function

        :param conditions: list of conditions to find objects
        :return: Sql object
        """
        return Sql.Sql.SELECTFROM(self.table.__table__).WHERE(**conditions)

    def new(self, **values):
        """
        creates and inserts new element of type self.table_name

        :param values: key value dict for obj
        :return: new instance of table model
        """
        Sql.Sql.INSERT(**values).INTO(self.table.__table__).do()
        return self.table(**values)
