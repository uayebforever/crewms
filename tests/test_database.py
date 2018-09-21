import pytest

import crewms

from crewms.bases import SQLAlchemyBase



def test_database_exists():


    print(SQLAlchemyBase.metadata.tables)

    # crewms.check_create_update_database()

    assert False
