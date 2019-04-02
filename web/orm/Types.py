# from . import Sql
from dataclasses import dataclass

from scanf import scanf


@dataclass
class DataType:
    name: str=None

    def __init__(self, length):
        self.name='{}({})'.format(
            self.name,
            length
        )


class Integer(DataType):
    name: str='INT'


class Text(DataType):
    name: str='TEXT'


class DateTime(DataType):
    name: str='DATETIME'


class Varchar(DataType):
    name: str='VARCHAR'


class Column:
    name: str=None
    data_type: DataType=None
    primary_key: bool=False
    nullable=None
    references=None
    on_delete=None

    def __init__(self, data_type, **kwargs):
        self.data_type=data_type
        default_attrs={
            'primary_key': False,
            'nullable'   : False,
            'references' : None,
            'on_delete'  : None,
        }

        for default_name, default_value in default_attrs.items():
            self.__setattr__(
                default_name,
                default_value \
                    if default_name not in kwargs \
                    else kwargs[default_name]
            )
        if self.references is not None:
            self.foreign_table, self.foreign_column=scanf('%s.%s', self.references)

    def set_name(self, name):
        self.name=name
        return self

    @property
    def sql(self):
        base='`{name}` {data_type}{primary_key}{nullable}'
        return base.format(
            name=self.name,
            data_type=self.data_type.name,
            primary_key=' PRIMARY KEY' if self.primary_key else '',
            nullable=' NOT NULL' if not self.nullable else ' NULL'
        )

    @property
    def ref_sql(self):
        base='FOREIGN KEY ({name}) REFERENCES {foreign_table}({foreign_column}){on_delete}'
        return base.format(
            name=self.name,
            foreign_table=self.foreign_table,
            foreign_column=self.foreign_column,
            on_delete='ON DELETE {}'.format(
                self.on_delete
            ) if self.on_delete is not None else ''
        ) if self.references is not None else ''
