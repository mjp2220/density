"""
Collects settings from the environment and adds them to the app configuration.

Flask specific settings will be set here and we can store additional settings
in the config object as well.
"""


from os import environ
from sys import exit


# dictionary the flask app configures itself from
config = {
    'HOST': '0.0.0.0',
    'PORT': None,
    'SECRET_KEY': None,
    'PG_USER': None,
    'PG_PASSWORD': None,
    'PG_DB': None,
    'PG_HOST': None,
    'PG_PORT': None,
    'GOOGLE_CLIENT_ID': None,
    'DEBUG': True if environ.get('DEBUG') == 'TRUE' else False
}

# consul_configurations contains equivalent keys that will be used to extract
# configuration values from Consul.
consul_configurations = [  # consul key --> config key
    ('flask_port', 'PORT'),
    ('secret_key', 'SECRET_KEY'),
    ('postgres_user', 'PG_USER'),
    ('postgres_password', 'PG_PASSWORD'),
    ('postgres_database', 'PG_DB'),
    ('postgres_host', 'PG_HOST'),
    ('postgres_port', 'PG_PORT'),
    ('google_client_id', 'GOOGLE_CLIENT_ID'),
]

if config.get('DEBUG'):

    try:  # use local settings
        for k, v in config:
            if not v:
                config[k] = environ[k]

    except KeyError as e:
        """ Throw an error if a setting is missing """
        print "ERR MSG: {}".format(e.message)
        print ("Some of your settings aren't in the environment."
               "You probably need to run:"
               "\n\n\tsource config/<your settings file>")
        exit(1)

else:  # prod w/ consul
    from consul import Consul
    kv = Consul().kv  # initalize client to KV store

    for k, v in consul_configurations:
        _, tmp = kv.get("density/{}".format(k))  # density is the root key
        val = tmp.get('Value')
        config[v] = val
        if not val:
            raise Exception("no val found in Consul for density/{}".format(k))

    # mail settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_DEFAULT_SENDER = 'densitylogger@gmail.com'
    MAIL_USERNAME = 'densitylogger@gmail.com'
    _, MAIL_PASSWORD = kv.get('density/mail_password')
    if not MAIL_PASSWORD:
        raise Exception("No password for Mail found in Consul")

    # administrator list
    ADMINS = [
        'bz2231@columbia.edu',
        'dzh2101@columbia.edu',
        'jgv2108@columbia.edu',
        'sb3657@columbia.edu',
        'mgb2163@columbia.edu',
        'jzf2101@columbia.edu'
    ]
