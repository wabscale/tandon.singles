from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from scanf import scanf

import tempfile
import hashlib
import imghdr
import string
import time
import os

from .app import db, app


def strptime(datestr):
    """
    Loads datetime from string for object
    """
    return datetime.strptime(datestr, '%Y-%m-%d %H:%M:%S')


def est_now():
    """
    Get EST now datetime object.

    .strftime('%Y-%m-%d %H:%M:%S')

    :return:
    """
    return datetime.now(tz=timezone(offset=timedelta(hours=-5)))


class Sql:
    """
    _type    : type of expression (select, insert, ...)
    _table   : str
    _tables  : [ self.Table ]
    _columns : str
    _joins   : [ str ]
    _where   : [ _Condition ]
    _attrs   : [ str ]

    _table: name of table being selected from
    _columns: names of columns being selected
    _joins: names of tables that are being joined
    _where: list of conditions to be applied
    _attrs: names of accessable attributes (foreign and local)

    __verbose_generation__ : bool
    __cache__   : dict
    """

    __verbose_generation__ = app.config['VERBOSE_SQL_GENERATION']
    __verbose_execution__ = False

    __cache__ = {
        'tables': {}
    }

    class ExpressionError(Exception):
        """
        Generic Exception, nothing special.
        """

    @dataclass
    class _Condition:
        attribute: str
        attribute_table: str
        value: str
        operator: str = None

        def __iter__(self):
            """
            This is here so that _Condition object can be unpacked
            """
            yield self.attribute
            yield self.attribute_table
            yield self.value
            yield self.operator

    @dataclass
    class _Attribute:
        table: str
        name: str

    class Table:
        column_info_sql = 'SELECT COLUMN_NAME, DATA_TYPE, COLUMN_KEY FROM INFORMATION_SCHEMA.COLUMNS ' \
            'WHERE TABLE_NAME = %s AND TABLE_SCHEMA = DATABASE();'

        @dataclass
        class _Column:
            name: str
            data_type: str
            primary_key: bool

            def __init__(self, name, date_type, primary_key):
                self.name, self.data_type, self.primary_key = name, date_type, True if primary_key == 'PRI' else False

            def __str__(self):
                return self.name

            # def __repr__(self):
            #     return self.name

        def __init__(self, name):
            self.name = name

            if name not in Sql.__cache__['tables']:
                self.columns = self._get_columns()
                Sql.__cache__['tables'][name] = self
            else:
                self.columns = Sql.__cache__['tables'][name].columns

        def _get_columns(self):
            """
            returns list of columsn for self.ref_table
            """
            with db.connect() as cursor:
                cursor.execute(
                    self.column_info_sql,
                    (self.name,)
                )
                return [
                    self._Column(*r)
                    for r in cursor.fetchall()
                ]

        def __str__(self):
            """
            Purly convience.
            """
            return self.name

    class JoinedTable(Table):
        """
        Provide this object with the name of the current table,
        and the table to join, and it will generate the sql to
        successfully join the tables together (with __str__).

        The sql generation is lazy
        """
        @dataclass
        class _JoinAttribute:
            name: str
            ref_name: str = None

            def is_same(self):
                return self.name == self.ref_name

        class JoinError(Exception):
            pass

        ref_info_sql = 'SELECT COLUMN_NAME, REFERENCED_COLUMN_NAME ' \
            'FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE ' \
            'WHERE TABLE_NAME = %s AND REFERENCED_TABLE_NAME = %s AND TABLE_SCHEMA = DATABASE();'

        def __init__(self, current_table, ref_table):
            super(self.__class__, self).__init__(ref_table)
            self.current_table = current_table.name
            self.join_attr = None
            self.sql = None

        @staticmethod
        def resolve_attribute(current_table, foreign_table):
            with db.connect() as cursor:
                cursor.execute(
                    Sql.JoinedTable.ref_info_sql,
                    (current_table, foreign_table,)
                )
                return cursor.fetchone()

        def _gen(self):
            """
            This will figure out foreign keys, then give back the proper
            sql to join the given tables.

            Errors will be raised if the join is not possible (if foreign
            keys not defined).
            """
            if self.sql is not None:
                return self.sql

            name, ref_name = self.resolve_attribute(self.current_table, self.name)

            self.join_attr = self._JoinAttribute(
                name=name,
                ref_name=ref_name
            )

            self.sql = 'JOIN {ref_table}'.format(
                ref_table=self.name
            ) if self.join_attr.is_same() else 'JOIN {ref_table} ON `{table}`.`{name}` = `{ref_table}`.`{ref_name}`'.format(
                table=self.current_table,
                ref_table=self.name,
                name=self.join_attr.name,
                ref_name=self.join_attr.ref_name,
            )
            return self.sql

        def __str__(self):
            return self._gen()

    def __init__(self):
        """
        Only needs to null out all the state attributes.
        """
        self._type           = None
        self._table          = None
        self._sql            = None
        self._attrs          = None
        self._result         = None

        # SELECT
        self._columns        = None
        self._joins          = None
        self._conditions     = None

        # INSERT
        self._insert_values  = None

        # UPDATE
        self._updates_values = None

    def __iter__(self):
        """
        Purely convenience.

        With this you can iterate through SELECT results
        """
        if self._type != 'SELECT':
            raise self.ExpressionError(
                'Iteration not possible'
            )
        yield from self()

    def __call__(self, *args, **kwargs):
        return self.all()

    def __len__(self):
        """
        Length of results
        """
        if self._result is None:
            self()
        return len(self._result)

    def __enter__(self):
        """
        __enter__ called in with statement. The intended behavior is that you
        make your expression in the with, then use as to set it to a variable,
        and it will execute the expression, and set the result to the variable.
        """
        return self.all()

    def __del__(self, *_):
        pass

    def do(self):
        """
        This is a cleaner name for insert queries to call to execute.

        :return: calls self.all()
        """
        return self.all()

    def _resolve_attribute(self, attr_name, skip_curr=False):
        """
        This method will take an attribute name, and
        try to find the table it came from. It will search
        in order starting with self._table, then iterate
        through self._joins.
        """
        if attr_name == '*':
            return self._table.name
        if not skip_curr:
            for column in self._table.columns:
                if column.name == attr_name:
                    return self._table.name
        if self._joins is not None:
            for joined_table in self._joins:
                for column in joined_table.columns:
                    if column == attr_name:
                        return joined_table.name
        raise self.ExpressionError(
            'Unable to resolve column name {}'.format(attr_name)
        )

    def _add_condition(self, clause, *specified_conditions, **conditions):
        """
        conditions will be resolved, while specified_conditions will not

        specfied_conditions will need to be of the form:
            '<table>.<column>=<value>'
            'Person.username=john'

        conditions will need to be of the form:
            <column>=<value>
            username=value

        :param clause: 'AND' or 'OR'
        :param specified_conditions: for when you want to be specific about conditions
        :param conditions: conditions that will be resolved
        """
        if self._conditions is None:
            self._conditions = []

        if self._type not in ('SELECT', 'UPDATE') or self._table is None:
            raise self.ExpressionError(
                'Expression Type error'
            )

        for condition in specified_conditions:
            table, attribute, value = scanf('%s.%s=%s', condition)

            if all(c in string.digits for c in value):
                value = int(value)

            if value in ('True', 'False'):
                value = 1 if value == 'True' else 0

            self._conditions.append(
                self._Condition(
                    operator=clause,
                    attribute=attribute,
                    attribute_table=table,
                    value=value,
                )
            )

        for attribute, value in conditions.items():
            attribute_table = self._resolve_attribute(attribute)
            self._conditions.append(
                self._Condition(
                    operator=clause,
                    attribute=attribute,
                    attribute_table=attribute_table,
                    value=value,
                )
            )

    def _generate_attributes(self):
        """
        Will fill self._attributes with self._Attributes for
        self._table and joined tables.
        """
        column_info_sql = 'SELECT COLUMN_NAME ' \
            'FROM INFORMATION_SCHEMA.COLUMNS ' \
            'WHERE TABLE_NAME = %s AND TABLE_SCHEMA = DATABASE();'
        joined_tables = list(map(
            lambda jt: jt.ref_table,
            self._joins
        )) if self._joins is not None else []
        all_tables = joined_tables + [self._table]
        for table_name in all_tables:
            with db.connect() as cursor:
                cursor.execute(
                    column_info_sql,
                    (table_name,)
                )
                current_table_attrs = cursor.fetchall()
                for attr in map(lambda x: x[0], current_table_attrs):
                    self._attrs.append(
                        self._Attribute(
                            table=table_name,
                            value=attr,
                        )
                    )

    def _generate_conditions(self):
        """
        This will hand back the sql as a string, and the
        args to fill the prepared placeholders

        ex:

        self._generate_conditions()
        ->
        "WHERE id = %i", (1,)
        """
        return (' ' + ' '.join(
            '{operator} `{table}`.`{attr}` = {placeholder}'.format(
                placeholder='%s',
                operator=operator,
                table=table,
                attr=attr,
            )
            for attr, table, value, operator in self._conditions
        ), [
            value if type(value) != bool else int(value)
            for _, _, value, _ in self._conditions
        ]) if self._conditions is not None else ('',[])

    def _generate_joins(self):
        """
        This method will hand back the sql for the
        joins in the expression.
        """
        return ' ' + ' '.join(
            str(joined_table)
            for joined_table in self._joins
        ) if self._joins is not None else ''

    def _generate_select_columns(self):
        return ', '.join('`{column_table}`.`{column_name}`'.format(
            column_table=self._resolve_attribute(column_name),
            column_name=column_name
        ) for column_name in self._columns) if self._columns != ['*'] else '*'

    def _generate_select(self):
        """
        Handle generation of sql for select expression.

        :return: sql_str, (args,)
        """
        if self._type != 'SELECT' or self._columns is None or self._table is None:
            raise self.ExpressionError(
                'Expression state incomplete'
            )

        base = 'SELECT {columns} FROM {table}{joins}{conditions};'

        table = '`{table}`'.format(table=self._table)
        columns = self._generate_select_columns()
        conditions, args = self._generate_conditions()
        joins = self._generate_joins()

        return base.format(
            conditions=conditions,
            columns=columns,
            table=table,
            joins=joins,
        ), args

    def _generate_insert(self):
        """
        This should hand back the prepared sql, and args for the insert values.
        """
        if self._type != 'INSERT' or self._table is None or self._insert_values is None:
            raise self.ExpressionError(
                'Expression state incomplete'
            )

        table = self._table
        columns = ', '.join('`{column_name}`'.format(
            column_name=column_name
        ) for column_name in self._insert_values.keys())
        values = ', '.join(
            ['%s'] * len(list(self._insert_values.values()))
        )

        sql = 'INSERT INTO `{table}` ({columns}) VALUES ({values});'.format(
            columns=columns,
            values=values,
            table=table,
        )

        return sql, list(
            value if type(value) != bool else int(value)
            for value in self._insert_values.values()
        )

    def _generate_set_values(self):
        """
        generates the condition
        :return:
        """
        return ', '.join(
            '`{column}` = %s'.format(
                column=column
            )
            for column in self._updates_values.keys()
        ), list(self._updates_values.values())

    def _generate_update(self):
        """
        generates sql statement for UPDATE expression
        :return:
        """
        if self._type != 'UPDATE' or self._table is None or self._updates_values is None:
            raise self.ExpressionError(
                'Expression state incomplete'
            )

        table = self._table
        values, args1 = self._generate_set_values()
        conditions, args2 = self._generate_conditions()

        base = 'UPDATE `{table}` SET {values}{conditions};'

        return base.format(
            table=table,
            values=values,
            conditions=conditions
        ), args1 + args2

    @staticmethod
    def _resolve_model(table_name):
        """
        Resolve the name of the table as a
        string to a BaseModel (else None).

        :param table_name: name of table to be resolved
        :return: subclass of BaseModel or None
        """
        models = BaseModel.__subclasses__()
        for model in models:
            if model.__table__ == table_name:
                return model
        return TempModel

    def gen(self):
        """
        This should take the object state, and convert it
        into a functioning sql statement, along with its arguments.

        This will hand back the sql statement, along with
        the args for it in a tuple.

        :return: sql_str, (args,)
        """
        if self._sql is None:
            self._sql = self._generate_select() \
                if self._type == 'SELECT' else \
                   self._generate_insert() \
                   if self._type == 'INSERT' else \
                       self._generate_update() \
                           if self._type == 'UPDATE' else ''

            if self.__verbose_generation__:
                print('Generated:', self._sql)
        return self._sql

    def first(self, use_cache=True):
        """
        :return: first element of results
        """
        self.gen()
        if self._result is None or not use_cache:
            if self.__verbose_execution__:
                print('Executing:', self._sql)
            with db.connect() as cursor:
                sql, args = self._sql
                cursor.execute(sql, args)
            if self._type == 'SELECT':
                Model = self._resolve_model(self._table.name)
                r = cursor.fetchone()

                if r is None:
                    self._result = None
                    return None

                kwargs = {
                    col.name: val
                    for col, val in zip(self._table.columns, r)
                }

                self._result = Model(**kwargs)

            else:  # insert or update
                self._result = True
        return self._result

    def all(self, use_cache=True):
        """
        This method should generate the sql, run it,
        then hand back the result (if expression type
        is SELECT).

        ** importaint to note that this does not
        handle pymysql.err.IntegrityError's

        ** If the expression type is a SELECT, the
        return value will be cursor.fetchall()

        *** If you select * out of a table, this will
        give you a list of initialized models. If the model
        has not been defined already, it will create a temporary
        model for you.
        """
        self.gen()
        if self._result is None or not use_cache:
            if self.__verbose_execution__:
                print('Executing:', self._sql)
            with db.connect() as cursor:
                sql, args = self._sql
                cursor.execute(sql, args)
            if self._type == 'SELECT':
                Model = self._resolve_model(self._table.name)

                model_init_kwargs = [
                    {
                        col.name: val
                        for col, val in zip(self._table.columns, item)
                    }
                    for item in cursor.fetchall()
                ]

                if len(model_init_kwargs) == 0:
                    return []

                self._result = [
                    Model(**kwargs)
                    for kwargs in model_init_kwargs
                ] if Model is not TempModel else [
                    Model(self._table.name, **kwargs)
                    for kwargs in model_init_kwargs
                ]

            else:  # insert or update
                self._result = True
        return self._result

    def WHERE(self, *specified_conditions, **conditions):
        """
        Errors will be raised if the type of this expression is not
        SELECT, or if a table has not been specified.

        If more than one condition is specified, it will by default
        apply AND logic between the conditions.
        """
        if self._type not in ('SELECT', 'UPDATE') or self._table is None or self._conditions is not None:
            raise self.ExpressionError(
                'Expression Type error'
            )

        self._conditions = list()
        self._add_condition('AND', *specified_conditions, **conditions)
        self._conditions[0].operator = 'WHERE'
        return self

    def INTO(self, table):
        """
        Sets table for INSERT expression.
        """
        if self._type != 'INSERT':
            raise self.ExpressionError(
                'Expression Type error'
            )

        if self._table is not None:
            raise self.ExpressionError(
                'Table already set for INSERT expression'
            )

        self._table = table
        return self

    def FROM(self, table):
        """
        Adds table to select from to expression state
        """
        if self._type != 'SELECT' or self._table is not None:
            raise self.ExpressionError(
                'Expression Type error'
            )
        self._table = self.Table(table)
        return self

    def JOIN(self, *tables):
        """
        Adds joins to expression state for tables.
        """
        if self._type != 'SELECT' or self._table is None:
            raise self.ExpressionError(
                'Expression Type error'
            )
        if self._joins is None:
            self._joins = list()
        for table in tables:
            self._joins.append(
                self.JoinedTable(self._table, table)
            )
        return self

    def AND(self, *specified_conditions, **conditions):
        if len(self._conditions) == 0:
            raise self.ExpressionError(
                'Use where clause before applying an AND'
            )
        self._add_condition('AND', *specified_conditions, **conditions)
        return self

    def OR(self, *specified_conditions, **conditions):
        if len(self._conditions) == 0:
            raise self.ExpressionError(
                'Use where clause before applying an OR'
            )
        self._add_condition('AND', *specified_conditions, **conditions)
        return self

    def SET(self, **kwargs):
        if self._type not in ('SELECT', 'UPDATE'):
            raise self.ExpressionError(
                'Invalid Expression Type'
            )
        self._updates_values = kwargs
        return self

    @staticmethod
    def UPDATE(table):
        """

        :param table:
        :return:
        """
        e = Sql()
        e._type = 'UPDATE'
        e._table = Sql.Table(table)
        return e

    @staticmethod
    def INSERT(**values):
        """
        First method that should be called in INSERT expression.
        """
        e = Sql()
        e._type = 'INSERT'
        e._insert_values = values
        return e

    @staticmethod
    def SELECT(*columns):
        """
        All this does is set the type for the expression
        to SELECT and the columns being selected.

        This will throw and error if an expression type has already
        been specified.
        """
        e = Sql()
        e._type = 'SELECT'
        e._columns = [ c for c in columns ]
        return e

    @staticmethod
    def SELECTFROM(table):
        """
        """
        return Sql.SELECT('*').FROM(table)


class BaseModel:
    """
    All subclasses just need to define their own __table__
    to be the name of the table (along with any other convince
    methods).
    """
    __table__ = None
    __columns__ = None
    __relationships__ = None

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
                    self.model_obj.__table__
                )

                self._objs = Sql.SELECTFROM(
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
        self.__columns__ = Sql.Table(self.__table__).columns
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
            self.__relationships__ = []

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
                value = strptime(value)
            elif col.data_type in ('int', 'tinyint'):
                value = int(value)
        self.__setattr__(col.name, value)

    def _set_state(self, **kwargs):
        for col, val in kwargs.items():
            self.__set_column_value(col, val)

    def commit(self):
        """
        generate and execute sql to update object in db
        :return:
        """
        Sql.UPDATE(self.__table__).SET(**{
            key: val
            for key, val in self.__columns__
        }).WHERE(**{
            key: val
            for key, val in self.__columns__
            if key in self.__primarykeys__
        })


class Query(object):
    def __init__(self, table):
        if isinstance(table, str):
            self.table_name = table
        try:
            self.table_name = table.__table__
        except AttributeError as e:
            raise Exception('Invalid query arguments {}'.format(e))

    def find(self, **conditions):
        """
        similar to sqlalchemy's Sql.filter_by function

        :param conditions: list of conditions to find objects
        :return: Sql object
        """
        return Sql.SELECTFROM(self.table_name).WHERE(**conditions)


class TempModel(BaseModel):
    """
    A temporary model
    """
    def __init__(self, table_name, *args, **kwargs):
        self.__table__ = table_name
        super(TempModel, self).__init__(*args, **kwargs)


class Person(BaseModel):
    __table__ = 'Person'
    __relationships__ = {
        'photos': 'Photo'
    }


class Photo(BaseModel):
    __table__ = 'Photo'

    @staticmethod
    def create(image, owner, caption, all_followers):
        """
        :param image:
        :param owner:
        :param caption:
        :param all_followers:
        :return: new photo object
        """

        filestream = image.data.stream
        with tempfile.NamedTemporaryFile() as f:
            f.write(filestream.read())
            filestream.seek(0)
            ext = imghdr.what(f.name)

        if ext not in ('png', 'jpeg', 'gif'):
            # handle invalid file
            return ext

        sha256 = lambda s: hashlib.sha256(s.encode()).hexdigest()

        filename = '{}.{}'.format(sha256('{}{}{}{}'.format(
            str(time.time()), caption, owner, os.urandom(0x10)
        )), ext)

        filedir = os.path.join(
            app.config['UPLOAD_DIR'],
            sha256(owner),
        )

        filepath = os.path.join(
            filedir,
            filename
        )

        os.makedirs(filedir, exist_ok=True)

        image.data.save(filepath)

        Sql.INSERT(
            allFollowers=all_followers,
            photoOwner=owner.username,
            timestamp=str(est_now()),
            filePath=filepath,
            caption=caption,
        ).INTO('Photo')()

    @staticmethod
    def owned_by(username):
        """
        Generates list of Photo object owner by username

        :param str username: owner of photos being selected
        :return: [
            Photo,
            ...
        ]
        """
        return [
            Sql.SELECTFROM('Photos').WHERE(owner=username)
        ]

    @staticmethod
    def visible_to(username):
        """
        Should give back all photo object that are visible to username

        TODO:
        need to make this order all photos by timestamp

        :return: [ Photo ]
        """
        return sorted(list(
            # photos that are in close friend groups that username is in
            Sql.SELECTFROM('Photos').JOIN('Share', 'CloseFriendGroup', 'Belong').WHERE(
                username=username
            )
        ) + list(
            # subscibed photos
            Sql.SELECTFROM('Photos').JOIN('Follow').WHERE(
                followeeUsername=username,
                acceptedfollow=True
            )
        ) + list(
            # users photos
            Sql.SELECTFROM('Photos').JOIN('Person').WHERE(
                username=username
            )
        ), key=lambda photo: photo.timestamp)


class User:
    """
    Base user class. Just give it a username, and it will attempt
    to load its information out of the database.
    """
    def __init__(self, username):
        self.username, self.password = (None,)*2
        self.person = Query(Person).find(username=username).first()
        if self.person is not None:
            self.username, self.password = self.person.username, self.person.password

    def check_password(self, pword):
        return check_password_hash(self.password, pword) if self.username is not None else False

    def is_authenticated(self):
        return self.username is not None

    def is_active(self):
        return True

    def is_anonymous(self):
        return self.username is None

    def get_id(self):
        return self.username

    def get_owned_photos(self):
        """
        :return list: Photo object owned by self.username
        """
        return Photo.owned_by(self.username)

    def get_feed(self):
        return Photo.visible_to(self.username)

    @staticmethod
    def create(username, password):
        """
        Make new user from username, password.

        :param str username:
        :param str password:
        :return User: new User object
        """
        password = generate_password_hash(password)
        print(password)
        Sql.INSERT(username=username, password=password).INTO('Person').do()
        return User(username)


# print(app.config['MYSQL_DATABASE_HOST'])
# User.create('admin', 'password')
# p = Query(Person).find(username='admin').first()
# print(list(p.photos))
# print(User('admin'))
# p = Sql.SELECTFROM('Person').WHERE(username='admin').execute()[0]
# print(p.photos)
# print(Sql.UPDATE('Photo').SET(photoID=1).WHERE(photoID=2).gen())
# print(*Sql.SELECT('username').FROM('Person').WHERE(username='j'))
# print(e.INSERT(username='d',password='pwrod').INTO('Person').execute())
