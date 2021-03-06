import os
import base64
import uuid
from datetime import datetime


TABLE_NAME = 'density_data'
QUERY_LIMIT = 100


def get_latest_data(cursor):
    """
    Gets the latest data for all group ids.

    :param cursor: cursor for our DB
    :return: list of dicts representing each row from the db
    :rtype: list of dict
    """
    query = """SELECT *
               FROM {table_name}
               WHERE dump_time=(
                   SELECT MAX(dump_time)
                   FROM {table_name}
               )
               ORDER BY group_name
               ;""".format(table_name=TABLE_NAME)
    cursor.execute(query)
    return cursor.fetchall()


def get_latest_group_data(cursor, group_id):
    """
    Gets latest dump of data for the specified group.

    :param cursor: cursor for our DB
    :param int group_id: id of the requested group
    :return:  list of dictionaries representing the rows corresponding to the
    query
    :rtype: list of dict
    """

    query = """SELECT *
               FROM {table_name}
               WHERE dump_time=(
                   SELECT MAX(dump_time)
                   FROM {table_name}
               ) AND group_id=%s
               ;""".format(table_name=TABLE_NAME)
    cursor.execute(query, [group_id])
    return cursor.fetchall()


def get_latest_building_data(cursor, parent_id):
    """
    Gets latest dump of data for the specified building.

    :param cursor: cursor for our DB
    :param int parent_id: id of the requested building
    :return:  list of dictionaries representing the rows corresponding to the
    query
    :rtype: list of dict
    """

    query = """SELECT *
               FROM {table_name}
               WHERE dump_time=(
                   SELECT MAX(dump_time)
                   FROM {table_name}
               ) AND parent_id=%s
               ;""".format(table_name=TABLE_NAME)
    cursor.execute(query, [parent_id])
    return cursor.fetchall()


def get_window_based_on_group(cursor, group_id, start_time, end_time, offset):
    """
    Gets all data for a group within a window. It will return the latest 100
    rows starting with the most recent ones.

    :param cursor: cursor for our DB
    :param int group_id: id of the group requested
    :param str start_time: start time of window
    :param str end_time: end time of the window
    :param int offset: how much to offset the query by
    :return: list of dictionaries representing the rows corresponding to the
    query
    :rtype: list of dict
    """
    query = """SELECT *
               FROM {table_name}
               WHERE (
                    dump_time >= %s
                    AND dump_time < %s
               ) AND group_id=%s
               ORDER BY dump_time DESC
               LIMIT %s
               OFFSET %s
               ;""".format(table_name=TABLE_NAME)
    cursor.execute(query, [start_time, end_time, group_id, QUERY_LIMIT,
                           offset])
    return cursor.fetchall()


def get_window_based_on_parent(cursor, parent_id, start_time, end_time,
                               offset):
    """
    Gets all data for a parent id (building) within a window. It will return
    the latest rows starting with the most recent ones.

    :param cursor: cursor for our DB
    :param int parent_id: id of the group requested
    :param str start_time: start time of window
    :param str end_time: end time of the window
    :param int offset: how much to offset the query by
    :return: list of dictionaries representing the rows corresponding to the
    query
    :rtype: list of dict
    """
    query = """SELECT *
               FROM {table_name}
               WHERE (
                    dump_time >= %s
                    AND dump_time < %s
               ) AND parent_id=%s
               ORDER BY dump_time DESC
               LIMIT %s
               OFFSET %s
               ;""".format(table_name=TABLE_NAME)
    cursor.execute(query, [start_time, end_time, parent_id, QUERY_LIMIT,
                           offset])
    return cursor.fetchall()


def get_cap_group(cursor):
    """
    Gets the max capacity of all groups. Equation for max capacity is average +
    std*2. We're estimating the 95th percentile as average + std*2.

    :param cursor: cursor for our DB
    :return: list of dictionaries representing the rows corresponding to the
    query
    :rtype: list of dict
    """

    query = """SELECT cast(
                          max(client_count)
                          as int
                       )  as capacity, group_id, group_name
               FROM {table_name}
               GROUP BY group_name, group_id
               ORDER BY group_name
               ;""".format(table_name=TABLE_NAME)
    cursor.execute(query)
    return cursor.fetchall()


def get_building_info(cursor):
    """
    Gets names and ids for groups and parents

    :param cursor:
    """
    query = """SELECT
                 group_name, group_id, parent_name, parent_id
                 FROM {table_name}
                 WHERE dump_time=(
                    SELECT MAX(dump_time)
                    FROM {table_name}
                 )
                 ORDER BY parent_name, group_name;
                 ;""".format(table_name=TABLE_NAME)
    cursor.execute(query)
    return cursor.fetchall()


def get_oauth_code_for_uni(cursor, uni):
    """
    :param str uni: UNI
    :return: code for the user (generates new code if doesn't exist)
    :rtype: str
    """
    # Try getting the code from the database.
    query = """SELECT code
               FROM oauth_data
               WHERE uni=%s LIMIT 1;"""
    cursor.execute(query, [uni])
    result = cursor.fetchone()

    if result is not None:
        return result['code']
    else:
        # If the code DNE, create a new one and insert into the database.
        token_bytes = os.urandom(32) + uuid.uuid4().bytes
        new_code = base64.urlsafe_b64encode(token_bytes)
        query = """INSERT INTO oauth_data (uni, code)
                   VALUES (%s, %s);"""
        cursor.execute(query, [uni, new_code])
        return new_code


def get_uni_for_code(cursor, code):
    """
    :param str code: oauth code
    :return: the uni for the user, or None if oauth code doesn't exist
    :rtype: str
    """
    query = """SELECT uni
               FROM oauth_data
               WHERE code=%s LIMIT 1;"""
    cursor.execute(query, [code])
    result = cursor.fetchone()
    if result is not None:
        return result['uni']


PARENTS = {
    '79': 'Lehman Library',
    '84': 'Lerner',
    '15': 'Northwest Corner Building',
    '75': 'John Jay',
    '103': 'Butler',
    '131': '',
    '146': 'Avery',
    '62': 'East Asian Library',
    '2': 'Uris'
}

def insert_density_data(cursor, data):
    query = """INSERT INTO {table_name} (dump_time, group_id, group_name,\
      parent_id, parent_name, client_count)
      VALUES %s;""".format(table_name=TABLE_NAME)

    date = datetime.now().replace(second=0, microsecond=0)

    db_success = True

    query = """INSERT INTO {table_name}
               (dump_time, group_id, group_name, parent_id,
                parent_name, client_count) VALUES
               (%s, %s, %s, %s, %s, %s);""".format(table_name=TABLE_NAME)

    data = [(date, int(key), data[key]['name'],
            int(data[key]['parent_id']), PARENTS[data[key]['parent_id']],
            int(data[key]['client_count'])) for key in data]

    try:
        cursor.executemany(query, data)
    except Exception as e:
        # At least log the error for our own sanity. But, we still
        # want to insert as many records as we can, so we won't break.
        print(e)
        db_success = False

    return db_success
