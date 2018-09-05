"""

This module contains tools necessary to access databases through SQLAlchemy.

A single database engine is created to connect to the database defined by the
configuration files. Then, a single `Session` is created for use in the
whole of application. This is per instructions from:

- http://docs.sqlalchemy.org/en/latest/orm/session_basics.html
- http://docs.sqlalchemy.org/en/latest/core/connections.html#basic-usage

The choice of the single session object may not be the best, but it has been
chosen for the reasons as follows:

- Some database engines can cause locking problems if one session is doing
  something that another session needs access to. Since FIDIA manages it's
  own state, it should not need to worry about another part of the same
  instance of FIDIA causing problems that would require Session level isolation
- There is a clear case for transaction level isolation (e.g. try..except blocks)
  This is already catered for by the `database_transaction` context manager.
- Having multiple sessions around causes problems where objects may belong to different
  sessions. So just dont.
- Having a single session may make some test cases easier to handle using monkey patching.

Note, however, it may be better to use the `sqlalchemy.pool.StaticPool` instead.

"""


from __future__ import absolute_import, division, print_function, unicode_literals


# from typing import List
# import crewms

# Python Standard Library Imports
from contextlib import contextmanager

# Other Library Imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Imports for is_sane_database
from sqlalchemy import inspect
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.declarative.clsregistry import _ModuleMarker
from sqlalchemy.orm import RelationshipProperty

# FIDIA Imports
from .local_config import config
from .bases import SQLAlchemyBase

# Set up logging
from . import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

__all__ = ['mappingdb_session']



if "sqlite" in config["MappingDatabase"]["engine"]:
    poolclass = QueuePool
else:
    poolclass = None
db_engine = create_engine("{engine}://{location}/{database}".format(
        engine=config["MappingDatabase"]["engine"],
        location=config["MappingDatabase"]["location"],
        database=config["MappingDatabase"]["database"]),
    echo=config["MappingDatabase"].getboolean("echo"),
    poolclass=poolclass,
    echo_pool=True
)
# db_engine = create_engine('sqlite:////Users/agreen/Desktop/fidia.sql', echo=True)

# A single session is used to access the Mapping Database for the whole of
# application. See docstring at the top of this file.
mappingdb_session = sessionmaker(bind=db_engine)()


@contextmanager
def database_transaction(session):
    """Provide a transaction scope around a series of database operations."""
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise

def check_create_update_database():
    """Update the database schema to match that required by FIDIA.

    This function should be called only AFTER all of FIDIA is loaded, e.g. at
    the end of the FIDIA `__init__.py` file. This is so that all of the database
    objects have been created, and the schema has stablized.

    This function should really do some sanity checking that the database schema
    has not changed if there is already an existing database that we are
    referencing. See the next function for some ideas.

    """

    SQLAlchemyBase.metadata.create_all(db_engine)

def is_sane_database(Base, session):
    """Check whether the current database matches the models declared in model base.

    Currently we check that all tables exist with all columns. What is not checked

    * Column types are not verified

    * Relationships are not verified at all (TODO)

    :param Base: Declarative Base for SQLAlchemy models to check

    :param session: SQLAlchemy session bound to an engine

    :return: True if all declared models have corresponding tables and columns.

    This is based on
    https://stackoverflow.com/questions/30428639/check-database-schema-matches-sqlalchemy-models-on-application-startup

    """

    engine = session.get_bind()
    iengine = inspect(engine)

    errors = False

    tables = iengine.get_table_names()

    # Go through all SQLAlchemy models
    for name, klass in Base._decl_class_registry.items():

        if isinstance(klass, _ModuleMarker):
            # Not a model
            continue

        table = klass.__tablename__
        if table in tables:
            # Check all columns are found
            # Looks like [{'default': "nextval('sanity_check_test_id_seq'::regclass)",
            #              'autoincrement': True, 'nullable': False, 'type': INTEGER(), 'name': 'id'}]

            columns = [c["name"] for c in iengine.get_columns(table)]
            mapper = inspect(klass)

            for column_prop in mapper.attrs:
                if isinstance(column_prop, RelationshipProperty):
                    # TODO: Add sanity checks for relations
                    pass
                else:
                    for column in column_prop.columns:
                        # Assume normal flat column
                        if not column.key in columns:
                            log.error(
                                "Model %s declares column %s which does not exist in database %s",
                                klass, column.key, engine)
                            errors = True
        else:
            log.error("Model %s declares table %s which does not exist in database %s", klass, table, engine)
            errors = True

    return not errors
