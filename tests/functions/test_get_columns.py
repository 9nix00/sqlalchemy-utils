import sqlalchemy as sa
from sqlalchemy_utils.functions import get_columns
from tests import TestCase


class TestGetColumns(TestCase):
    def create_models(self):
        class Building(self.Base):
            __tablename__ = 'building'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            name = sa.Column('_name', sa.Unicode(255))

        self.Building = Building

    def test_table(self):
        assert isinstance(
            get_columns(self.Building.__table__),
            sa.sql.base.ImmutableColumnCollection
        )

    def test_declarative_class(self):
        assert isinstance(
            get_columns(self.Building),
            sa.util._collections.OrderedProperties
        )

    def test_declarative_object(self):
        assert isinstance(
            get_columns(self.Building()),
            sa.util._collections.OrderedProperties
        )
