from . import Sql
from . import utils


class BaseModel:
    """
    All subclasses just need to define their own __table__
    to be the name of the table (along with any other convince
    methods).
    """
    __table__: str = None
    __columns__: list = None
    __relationships__: dict = None
    primary_keys: list = None

    class ModelError(Exception):
        pass

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
            self.foreign_table = Sql.Table(foreign_table)
            self._objs = None

        def __iter__(self):
            """
            yeild foreign table object specified my relationship
            :return:
            """

            if self._objs is None:
                ref, curr = Sql.JoinedTable.resolve_attribute(
                    self.foreign_table.name,
                    self.model_obj.__table__,
                )

                self._objs = Sql.Sql.SELECTFROM(
                    self.foreign_table.name
                ).JOIN(self.model_obj.__table__).WHERE(
                    '{table}.{primarykey}={value}'.format(
                        table=self.foreign_table.name,
                        primarykey=ref,
                        value=self.model_obj.__getattr__(curr)
                    )
                ).all()

            yield from self._objs

    def __init__(self, **kwargs):
        """
        Will fetch names of columns when initially called.

        :param list args: list of data members for object in order they were created.
        """
        table = Sql.Table(self.__table__)
        self.__columns__ = table.columns
        self.__relationships__ = table.relationships
        self.__lower_relationships__ = list(map(
            lambda rel: rel.lower(),
            self.__relationships__
        ))
        self.__column_lot__ = {
            col.column_name: col
            for col in self.__columns__
        }

        self.primary_keys = list(filter(
            lambda column: column.primary_key,
            self.__columns__
        ))

        self._set_state(**kwargs)

    def __str__(self):
        return '<{}Model: {}>'.format(
            self.__table__,
            '{{\n{}\n}}'.format(',\n'.join(
                '    {:12}: {}'.format(
                    col.column_name,
                    str(self.__dict__[col.column_name])
                )
                for col in self.__columns__
            ))
        )

    def __setattr__(self, key, value):
        if 'primary_keys' in self.__dict__ and key in self.__dict__['primary_keys']:
            raise self.__dict__['ModelError']('Unable to modify primary key value')
        self.__dict__[key] = value
        # setattr(self, key, value)

    def __getattr__(self, item):
        """
        this is where relationships will be lazily resolved.
        :return:
        """
        if item in self.__dict__:
            return self.__dict__[item]
        if item in self.__lower_relationships__:
            self.__dict__[item] = self.Relationship(
                self,
                item[0].upper() + item[1:]
            )
            return self.__dict__[item]
        if item.endswith('s') and item[:-1] in self.__lower_relationships__:
            self.__dict__[item] = self.Relationship(
                self,
                item[0].upper() + item[1:-1]
            )
            return self.__dict__[item]
        raise AttributeError('{} not found'.format(item))

    def _generate_relationships(self):
        """
        :return:
        """
        for table_name in self.__relationships__:
            self.__setattr__(
                table_name,
                self.Relationship(self, table_name)
            )

    def __set_column_value(self, column_name, value):
        col = self.__column_lot__[column_name]
        if value is not None:
            if col.data_type == 'timestamp' and type(value) == str:
                value = utils.utils.strptime(value)
            elif col.data_type in ('int', 'tinyint'):
                value = int(value)
        self.__setattr__(col.column_name, value)

    def _set_state(self, **kwargs):
        for col in self.__columns__:
            self.__set_column_value(col.column_name, None)
        for col, val in kwargs.items():
            self.__set_column_value(col, val)

    def update(self):
        """
        generate and execute sql to update object in db

        ** This will rely on primary keys to update the object. If
        primary keys are modified, this will likely crash.

        :return:
        """
        Sql.Sql.UPDATE(self.__table__).SET(**{
            col.column_name: self.__getattr__(col.column_name)
            for col in self.__columns__
            if not col.primary_key
        }).WHERE(**{
            col.column_name: self.__getattr__(col.column_name)
            for col in self.__columns__
            if col.primary_key
        }).do()


class TempModel(BaseModel):
    """
    A temporary model
    """

    def __init__(self, table_name, *args, **kwargs):
        self.__table__ = table_name
        super(TempModel, self).__init__(*args, **kwargs)

    def __str__(self):
        return '<Temp{}Model: {}>'.format(
            self.__table__,
            '{{\n{}\n}}'.format(',\n'.join(
                '    {:12}: {}'.format(
                    col.column_name,
                    str(self.__dict__[col.column_name])
                )
                for col in self.__columns__
            ))
        )
