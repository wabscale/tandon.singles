from datetime import datetime, timedelta, timezone


class utils:
    @staticmethod
    def strptime(datestr):
        """
        Loads datetime from string for object
        """
        return datetime.strptime(datestr, '%Y-%m-%d %H:%M:%S')

    @staticmethod
    def est_now():
        """
        Get EST now datetime object.

        .strftime('%Y-%m-%d %H:%M:%S')

        :return:
        """
        return datetime.now(tz=timezone(offset=timedelta(hours=-5)))
