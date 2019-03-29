from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
from werkzeug import secure_filename
from dataclasses import dataclass
from scanf import scanf
import string
import os

from .app import db, app


def est_now():
    """
    Get EST now datetime object.
    :return:
    """
    return datetime.now(tz=timezone(offset=timedelta(hours=-5)))


class SQL:
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

    __verbose__: bool
    """

    __verbose__ = True

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

        def __init__(self, current_table, joins, ref_table):
            super(self.__class__, self).__init__(ref_table)
            self.current_table = current_table.name
            self.joins = joins
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
            res = None

            for table_name in [self.name] + self.joins:
                with db.connect() as cursor:
                    cursor.execute(
                        self.ref_info_sql,
                        (table_name, self.current_table,)
                    )
                    res = cursor.fetchone()
                    if res is not None:
                        break

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
        self._sql           = None
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
        if attr_name == '*':
            return self._table.name
        for column in self._table.columns:
            if column == attr_name:
                return self._table.name
        for joined_table in self._joins:
            for column in joined_table.columns:
                if column == attr_name:
                    return joined_table.name

    @staticmethod
    def INSERT(**values):
        """
        First method that should be called in INSERT expression.
        """
        e = SQL()
        e._type = 'INSERT'
        e._insert_values = values
        return e

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

    @staticmethod
    def SELECT(*columns):
        """
        All this does is set the type for the expression
        to SELECT and the columns being selected.

        This will throw and error if an expression type has already
        been specified.
        """
        e = SQL()
        e._type = 'SELECT'
        e._columns = list(c for c in columns)
        return e

    def FROM(self, table):
        """

        """
        if self._type != 'SELECT' or self._table is not None:
            raise self.ExpressionError(
                'Expression Type error'
            )
        self._table = self._Table(table)
        return self

    def JOIN(self, *tables):
        """

        """
        if self._type != 'SELECT' or self._table is None:
            raise self.ExpressionError(
                'Expression Type error'
            )
        if self._joins is None:
            self._joins = list()
        for table in tables:
            self._joins.append(
                self._JoinedTable(self._table, self._joins, table)
            )
        return self

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
        if self._type != 'SELECT' or self._table is None or self._conditions is not None:
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

    def WHERE(self, *specified_conditions, **conditions):
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
        self._add_condition('AND', *specified_conditions, **conditions)
        self._conditions[0].operator = 'WHERE'
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
                '%i' if type(value) in (int,bool,) else '',
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
            '%s' if type(value) == str else '%i' if type (value) in (int,bool,) else ''
            for value in self._insert_values.values()
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
                   if self._type == 'INSERT' else ''
            if self.__verbose__:
                print(self._sql)
        return self._sql

    def execute(self):
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
        with db.connect() as cursor:
            cursor.execute(
                *self._sql
            )
            if self._type == 'SELECT' and self._columns == ['*']:
                Model = self._resolve_model(self._table.name)
                return [
                    Model(*args)
                    for args in cursor.fetchall()
                ] if Model is not TempModel else [
                    Model(self._table.name, *args)
                    for args in cursor.fetchall()
                ]

            return cursor.fetchall() if self._type == 'SELECT' else None

    def __iter__(self):
        """
        Purely convenience.

        With this you can iterate through SELECT results
        """
        if self._type != 'SELECT':
            raise self.ExpressionError(
                'Iteration not possible'
            )
        yield from self.execute()


class BaseModel:
    """
    All subclasses just need to define their own __table__
    to be the name of the table (along with any other convince
    methods).
    """
    __table__ = None
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

            self.__columns__ = SQL._Table(self.__table__).columns
            self.__columns__ = list(map(lambda x: x[0], self.__columns__))

        for key, val in zip(self.__columns__, args):
            self.__setattr__(key, val)


class TempModel(BaseModel):
    """
    A temporary model
    """
    def __init__(self, table_name, *args):
        self.__table__ = table_name
        super(TempModel, self).__init__(*args)


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
        SQL.INSERT(
            allFollowers=all_followers,
            photoOwner=owner.username,
            timestamp=str(est_now()),
            filePath=file_path,
            caption=caption,
        ).INTO('Photo').execute()

    @staticmethod
    def ownded_by(username):
        """
        Generates list of Photo object owner by username

        :param str username: owner of photos being selected
        :return: [
            Photo,
            ...
        ]
        """
        return [
            Photo(*photo)
            for photo in SQL.SELECT('*').FROM('Photos').WHERE(owner=username).execute()
        ]

    @staticmethod
    def visible_to(username):
        """
        Should give back all photo object that are visible to username

        TODO:
        need to make this order all photos by timestamp

        :return: [ Photo ]
        """
        return [
            # photos that are in close friend groups that username is in
            Photo(*photo)
            for photo in SQL.SELECT('*').From('Photos').JOIN('Share').JOIN('CloseFriendGroup').JOIN('Belong').WHERE(
                    username=username
            ).execute()
        ] + [
            # subscibed photos
            Photo(*photo)
            for photo in SQL.SELECT('*').FROM('Photos').JOIN('Follow').WHERE(
                    followeeUsername=username,
                    acceptedfollow=True
            ).execute()
        ] + [
            # users photos
            Photo(*photo)
            for photo in SQL.SELECT('*').FROM('Photos').JOIN('Person').WHERE(
                    username=username
            ).execute()
        ]


class User:
    """
    Base user class. Just give it a username, and it will attempt
    to load its information out of the database.
    """
    def __init__(self, username):
        self.username, self.password = (None,)*2
        res = SQL.SELECT('username', 'password').FROM('Person').WHERE(username=username).execute()
        if len(res) == 1:
            self.username, self.password = res[0]

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
        SQL.INSERT(username=username, password=password).INTO('Person').execute()
        return User(username)


print(*SQL.SELECT('*').FROM('Person'))
# print(e.INSERT(username='d',password='pwrod').INTO('Person').execute())
