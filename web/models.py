from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
from werkzeug import secure_filename
from dataclasses import dataclass
import os

from .app import db, app


def est_now():
    """
    Get EST now datetime object.
    :return:
    """
    return datetime.now(tz=timezone(offset=timedelta(hours=-5)))


class Expression:
    """
    _type    : type of expression (select, insert, ...)
    _table   : str
    _tables  : [ self._Table ]
    _columns : str
    _joins   : [ str ]
    _where   : [ _Condition ]
    _attrs   : [ str ]

    _table: name of table being selected from
    _columns: names of columns being selected
    _joins: names of tables that are being joined
    _where: list of conditions to be applied
    _attrs: names of accessable attributes (foreign and local)
    """

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

    class _Table:
        column_info_sql = 'SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS ' \
            'WHERE TABLE_NAME = %s AND TABLE_SCHEMA = DATABASE();'

        def __init__(self, name):
            self.name = name
            self.columns = self._get_columns()

        def _get_columns(self):
            """
            returns list of columsn for self.ref_table
            """
            with db.connect() as cursor:
                cursor.execute(
                    self.column_info_sql,
                    (self.name,)
                )
                return list(map(
                    lambda col: col[0],
                    cursor.fetchall()
                ))

        def __str__(self):
            """
            Purly convience.
            """
            return self.name

    class _JoinedTable(_Table):
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


        def _gen(self):
            """
            This will figure out foreign keys, then give back the proper
            sql to join the given tables.

            Errors will be raised if the join is not possible (if foreign
            keys not defined).
            """
            if self.sql is not None:
                return self.sql
            with db.connect() as cursor:
                cursor.execute(
                    self.ref_info_sql,
                    (self.name, self.current_table,)
                )
                res = cursor.fetchone()

                if res is None: # sanity check
                    raise self.JoinError(
                        'Invalid Join'
                    )

                ref_name, name = res
                self.join_attr = self._JoinAttribute(
                    name=name,
                    ref_name=ref_name
                )

            self.sql =  'JOIN {ref_table}'.format(
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
        self._type          = None
        self._table         = None
        self._attrs         = None

        # SELECT
        self._columns       = None
        self._joins         = None
        self._conditions    = None

        # INSERT
        self._insert_values = None

    def __enter__(self):
        """
        __enter__ called in with statement. The intended behavior is that you
        make your expression in the with, then use as to set it to a variable,
        and it will execute the expression, and set the result to the variable.

        eg:

        with Expression().select('*')._from('Users') as users:
            print(users)

        (
            id,
            username,
            password
        ),
        ...

        """
        return self.execute()

    def __del__(self, *_):
        pass

    def _resolve_attribute(self, attr_name):
        """
        This method will take an attribute name, and
        try to find the table it came from. It will search
        in order starting with self._table, then iterate
        through self._joins.
        """
        for column in self._table.columns:
            if column == attr_name:
                return self._table.name
        for joined_table in self._joins:
            for column in joined_table:
                if column == attr_name:
                    return joined_table.name

    def INSERT(self, **values):
        """
        First method that should be called in INSERT expression.
        """
        if self._type is not None:
            raise self.ExpressionError(
                'Expressions Type error'
            )

        if self._insert_values is not None:
            raise self.ExpressionError(
                'Insert Expression values already set'
            )

        self._type = 'INSERT'
        self._insert_values = values
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

    def SELECT(self, *columns):
        """
        All this does is set the type for the expression
        to SELECT and the columns being selected.

        This will throw and error if an expression type has already
        been specified.
        """
        if self._type is not None:
            raise self.ExpressionError(
                'Expression Type error'
            )
        self._type = 'SELECT'
        self._columns = columns
        return self

    def FROM(self, table):
        """

        """
        if self._type != 'SELECT' or self._table is not None:
            raise self.ExpressionError(
                'Expression Type error'
            )
        self._table = self._Table(table)
        return self

    def JOIN(self, table):
        """

        """
        if self._type != 'SELECT' or self._table is None:
            raise self.ExpressionError(
                'Expression Type error'
            )
        if self._joins is None:
            self._joins = list()
            self._joins.append(
                self._JoinedTable(self._table, table)
            )
        return self

    def WHERE(self, **condition):
        """
        Errors will be raised if the type of this expression is not
        SELECT, or if a table has not been specified.

        If more than one condition is specified, it will by default
        apply AND logic between the conditions.
        """
        if self._type != 'SELECT' or self._table is None or self._conditions is not None:
            raise self.ExpressionError(
                'Expression Type error'
            )

        self._conditions = list()

        for attribute, value in condition.items():
            attribute_table = self._resolve_attribute(attribute)
            self._conditions.append(
                self._Condition(
                    operator='AND',
                    attribute=attribute,
                    attribute_table=attribute_table,
                    value=value,
                )
            )

        self._conditions[0].operator = 'WHERE'
        return self

    def AND(self, **condition):
        if self._type != 'SELECT' or self._table is None:
            raise self.ExpressionError()

        if len(self._conditions) == 0:
            raise self.ExpressionError(
                'Use where clause before applying an AND'
            )

        for attribute, value in condition.items():
            attribute_table = self._resolve_attribute(attribute)
            self._conditions.append(
                self._Condition(
                    operator='AND',
                    attribute=attribute,
                    attribute_table=attribute_table,
                    value=value,
                )
            )
        return self

    def OR(self, **conditions):
        if self._type != 'SELECT' or self._table is None:
            raise self.ExpressionError()

        if len(self._conditions) == 0:
            raise self.ExpressionError(
                'Use where clause before applying an OR'
            )

        for attribute, value in conditions.items():
            attribute_table = self._resolve_attribute(attribute)
            self._conditions.append(
                self._Condition(
                    operator='OR',
                    attribute=attribute,
                    attribute_table=attribute_table,
                    value=value,
                )
            )
        return self

    def _generate_attributes(self):
        """
        Will fill self._attributes with self._Attributes for
        self._table and joined tables.
        """
        column_info_sql = 'SELECT COLUMN_NAME ' \
            'FROM INFORMATION_SCHEMA.COLUMNS ' \
            'WHERE TABLE_NAME = %s AND TABLE_SCHEMA = DATABASE();'
        joined_tables =  list(map(lambda jt: jt.ref_table, self._joins)) if self._joins is not None else []
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
                placeholder='%s' if type(value) == str else
                            '%i' if type(value) == int else '',
                operator=operator,
                table=table,
                attr=attr,
            )
            for attr, table, value, operator in self._conditions
        ), [
            value
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
        columns = ', '.join('`{column_table}`.`{column_name}`'.format(
            column_table=self._resolve_attribute(column_name),
            column_name=column_name
        ) for column_name in self._columns)
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

        table=self._table
        columns = ', '.join('`{column_name}`'.format(
            column_name=column_name
        ) for column_name in self._insert_values.keys())
        values = ', '.join(
            '%s' if type(value) == str else '%i' if type (value) == int else ''
            for value in self._insert_values.values()
        )

        sql = 'INSERT INTO {table} ({columns}) VALUES ({values});'.format(
            columns=columns,
            values=values,
            table=table,
        )

        return sql, list(
            self._insert_values.values()
        )

    def gen(self):
        """
        This should take the object state, and convert it
        into a functioning sql statement, along with its arguments.

        This will hand back the sql statement, along with
        the args for it in a tuple.

        :return: sql_str, (args,)
        """
        return self._generate_select() \
            if self._type == 'SELECT' else \
               self._generate_insert() \
               if self._type == 'INSERT' else ''

    def execute(self):
        """
        This method should generate the sql, run it,
        then hand back the result (if expression type
        is SELECT).

        ** importaint to note that this does not
        handle pymysql.err.IntegrityError's

        ** If the expression type is a SELECT, the
        return value will be cursor.fetchall()
        """
        with db.connect() as cursor:
            cursor.execute(
                *self.gen()
            )
            return cursor.fetchall() if self._type == 'SELECT' else None


class BaseModel:
    """
    All subclasses just need to define their own __table__
    to be the name of the table (along with any other convince
    methods).
    """
    __table__ = None
    __schemata__ = 'TS'
    __columns__ = None
    __foreign_tables__ = None

    def __init__(self, *args):
        """
        Will fetch names of columns when initially called.

        :param list args: list of data members for object in order they were created.
        """
        if self.__columns__ is None:
            if self.__table__ is None:
                raise NotImplementedError('__table__ not implemented')

            with db.connect() as cursor:
                _attrs = cursor.execute(
                    'SELECT COLUMN_NAME FROM information_schema.columns '
                    'WHERE TABLE_SCHEMATA = %s AND TABLE_NAME = %s;',
                    (self.__schemata__, self.__table__)
                )
                cursor.fetchall()
                self.__columns__ = list(map(lambda x: x[0], _attrs))

        for key, val in zip(self.__columns__, args):
            self.__setattr__(key, val)

    def __getattribute__(self, key):
        """
        I want this to lazy load out foreign attributes.
        """
        if key in self.__dir__:
            return self.__dir__[key]


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
        file_path=os.path.join(
            app.config['UPLOAD_FOLDER'],
            secure_filename(image.data.filename)
        )
        image.data.save()
        with db.connect() as cursor:
            cursor.execute(
                'INSERT INTO Photo (photoOwner, timestamp, filePath, caption, allFollowers) '
                'VALUES (%s, %s, %s, %s, %i)',
                (owner.username, str(est_now()), file_path, caption, all_followers)
            )

    @staticmethod
    def get_photos_by_owner(username):
        """
        Generates list of Photo object owner by username

        :param str username: owner of photos being selected
        :return: [
            Photo,
            ...
        ]
        """
        with db.connect() as cursor:
            cursor.execute(
                'SELECT * FROM Photos '
                'JOIN Person '
                'WHERE Person.owner = %s',
                (username,)
            )
            return [
                Photo(*photo)
                for photo in cursor.fetchall()
            ]


class User:
    """
    Base user class. Just give it a username, and it will attempt
    to load its information out of the database.
    """
    def __init__(self, username):
        self.username, self.password = (None,)*2
        with db.connect() as cursor:
            cursor.execute(
                'SELECT username, password '
                'FROM Person '
                'WHERE username = %s;',
                (username,)
            )
            res = cursor.fetchone()
            if res is not None:
                self.username, self.password = res

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

    def get_photos(self):
        """
        :return list: Photo object owned by self.username
        """
        return Photo.get_photos_by_owner(self.username)

    @staticmethod
    def create(username, password):
        """
        Make new user from username, password.

        :param str username:
        :param str password:
        :return User: new User object
        """
        with db.connect() as cursor:
            cursor.execute(
                'INSERT INTO Person (username, password) VALUES '
                '(%s, %s);',
                (username, generate_password_hash(password),)
            )
        return User(username)


# print(Expression().SELECT('username').FROM('Person').JOIN('Photo').WHERE(username='abc').gen())
