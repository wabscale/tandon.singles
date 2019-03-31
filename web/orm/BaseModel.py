import web.orm.Sql
from .utils import utils


class BaseModel:
    """
    All subclasses just need to define their own __table__
    to be the name of the table (along with any other convince
    methods).
    """
    __table__: str = None
    __columns__: list = None
    __relationships__: dict = None

    class Relationship:
        """
        class BaseModel:
            __table__ = 'Person'
            __relationships__ = {
                'photos': 'Photo'
            }
        """

        def __init__(self, model_obj, foreign_table):
            self.model_obj = model_obj
            self.foreign_table = web.orm.Sql.Table(foreign_table)
            self._objs = None

        def __iter__(self):
            """
            yeild foreign table object specified my relationship
            :return:
            """

            if self._objs is None:
                ref, curr = web.orm.Sql.JoinedTable.resolve_attribute(
                    self.foreign_table.name,
                    self.model_obj.__table__
                )

                self._objs = web.orm.Sql.Sql.SELECTFROM(
                    self.foreign_table.name
                ).JOIN(self.model_obj.__table__).WHERE(
                    '{table}.{primarykey}={value}'.format(
                        table=self.foreign_table.name,
                        primarykey=ref,
                        value=self.model_obj.__getattr__(curr)
                    )
                ).all()

            yield from self._objs

    def __init__(self, *args, **kwargs):
        """
        Will fetch names of columns when initially called.

        :param list args: list of data members for object in order they were created.
        """
        self.__columns__ = web.orm.Sql.Table(self.__table__).columns
        self.__column_lot__ = {
            col.name: col
            for col in self.__columns__
        }

        self.__primarykeys__ = list(filter(
            lambda column: column.primary_key,
            self.__columns__
        ))

        # self._set_state(**{
        #     col.name: eval
        #     for col, val in zip(self.__columns__, kwargs)
        # })
        # print('\n'.join('{} : {}'.format(k, v) for k, v in self.__dict__.items()))
        self._set_state(**kwargs)

        if self.__relationships__ is None:
            self.__relationships__ = {}

    def __str__(self):
        return '<{}Model: {}>'.format(
            self.__table__,
            '{{\n{}\n}}'.format(',\n'.join(
                '    {:12}: {}'.format(col.name, str(self.__dict__[col.name]))
                for col in self.__columns__
            ))
        )

    def __getattr__(self, item):
        """
        this is where relationships will be lazily resolved.
        :return:
        """
        if item in self.__dict__:
            return self.__dict__[item]
        if item in self.__relationships__:
            self.__dict__[item] = self.Relationship(
                self,
                self.__relationships__[item]
            )
            return self.__dict__[item]
        raise AttributeError('{} not found'.format(item))

    def _generate_relationships(self):
        """
        :return:
        """
        for rel_name, table_name in self.__relationships__.items():
            self.__setattr__(
                rel_name,
                self.Relationship(self, table_name)
            )

    def __set_column_value(self, column_name, value):
        col = self.__column_lot__[column_name]
        if value is not None:
            if col.data_type == 'timestamp' and type(value) == str:
                value = utils.strptime(value)
            elif col.data_type in ('int', 'tinyint'):
                value = int(value)
        self.__setattr__(col.name, value)

    def _set_state(self, **kwargs):
        for col in self.__columns__:
            self.__set_column_value(col.name, None)
        for col, val in kwargs.items():
            self.__set_column_value(col, val)

    def commit(self):
        """
        generate and execute sql to update object in db

        ** This will rely on primary keys to update the object. If
        primary keys are modified, this will likely crash.

        :return:
        """
        web.orm.Sql.Sql.UPDATE(self.__table__).SET(**{
            key: val
            for key, val in self.__columns__
        }).WHERE(**{
            key: val
            for key, val in self.__columns__
            if key in self.__primarykeys__
        })


class TempModel(BaseModel):
    """
    A temporary model
    """

    def __init__(self, table_name, *args, **kwargs):
        self.__table__ = table_name
        super(TempModel, self).__init__(*args, **kwargs)
