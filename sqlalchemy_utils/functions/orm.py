import sqlalchemy as sa


def remove_property(class_, name):
    """
    **Experimental function**

    Remove property from declarative class
    """
    mapper = class_.mapper
    table = class_.__table__
    columns = class_.mapper.c
    column = columns[name]
    del columns._data[name]
    del mapper.columns[name]
    columns._all_cols.remove(column)
    mapper._cols_by_table[table].remove(column)
    mapper.class_manager.uninstrument_attribute(name)
    del mapper._props[name]


def primary_keys(class_):
    """
    Returns all primary keys for given declarative class.
    """
    for column in class_.__table__.c:
        if column.primary_key:
            yield column


def table_name(obj):
    """
    Return table name of given target, declarative class or the
    table name where the declarative attribute is bound to.
    """
    class_ = getattr(obj, 'class_', obj)

    try:
        return class_.__tablename__
    except AttributeError:
        pass

    try:
        return class_.__table__.name
    except AttributeError:
        pass


def local_column_names(prop):
    if not hasattr(prop, 'secondary'):
        yield prop._discriminator_col.key
        yield prop._id_col.key
    elif prop.secondary is None:
        for local, _ in prop.local_remote_pairs:
            yield local.name
    else:
        if prop.secondary is not None:
            for local, remote in prop.local_remote_pairs:
                for fk in remote.foreign_keys:
                    if fk.column.table in prop.parent.tables:
                        yield local.name


def remote_column_names(prop):
    if not hasattr(prop, 'secondary') or prop.secondary is None:
        for _, remote in prop.local_remote_pairs:
            yield remote.name
    else:
        for _, remote in prop.local_remote_pairs:
            for fk in remote.foreign_keys:
                if fk.column.table in prop.parent.tables:
                    yield remote.name


def declarative_base(model):
    """
    Returns the declarative base for given model class.

    :param model: SQLAlchemy declarative model
    """
    for parent in model.__bases__:
        try:
            parent.metadata
            return declarative_base(parent)
        except AttributeError:
            pass
    return model


def has_changes(obj, attr):
    """
    Simple shortcut function for checking if given attribute of given
    declarative model object has changed during the transaction.


    ::


        from sqlalchemy_utils import has_changes


        user = User()

        has_changes(user, 'name')  # False

        user.name = u'someone'

        has_changes(user, 'name')  # True


    :param obj: SQLAlchemy declarative model object
    :param attr: Name of the attribute
    """
    return (
        sa.inspect(obj)
        .attrs
        .get(attr)
        .history
        .has_changes()
    )


def identity(obj):
    """
    Return the identity of given sqlalchemy declarative model instance as a
    tuple. This differs from obj._sa_instance_state.identity in a way that it
    always returns the identity even if object is still in transient state (
    new object that is not yet persisted into database).

    ::

        from sqlalchemy import inspect
        from sqlalchemy_utils import identity


        user = User(name=u'John Matrix')
        session.add(user)
        identity(user)  # None
        inspect(user).identity  # None

        session.flush()  # User now has id but is still in transient state

        identity(user)  # (1,)
        inspect(user).identity  # None

        session.commit()

        identity(user)  # (1,)
        inspect(user).identity  # (1, )


    .. versionadded: 0.21.0

    :param obj: SQLAlchemy declarative model object
    """
    id_ = []
    for column in sa.inspect(obj.__class__).columns:
        if column.primary_key:
            id_.append(getattr(obj, column.name))

    if all(value is None for value in id_):
        return None
    else:
        return tuple(id_)


def naturally_equivalent(obj, obj2):
    """
    Returns whether or not two given SQLAlchemy declarative instances are
    naturally equivalent (all their non primary key properties are equivalent).


    ::

        from sqlalchemy_utils import naturally_equivalent


        user = User(name=u'someone')
        user2 = User(name=u'someone')

        user == user2  # False

        naturally_equivalent(user, user2)  # True


    :param obj: SQLAlchemy declarative model object
    :param obj2: SQLAlchemy declarative model object to compare with `obj`
    """
    for prop in sa.inspect(obj.__class__).iterate_properties:
        if not isinstance(prop, sa.orm.ColumnProperty):
            continue

        if prop.columns[0].primary_key:
            continue

        if not (getattr(obj, prop.key) == getattr(obj2, prop.key)):
            return False
    return True
