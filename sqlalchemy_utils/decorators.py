from collections import defaultdict
import itertools
import sqlalchemy as sa
import six


class AttributeValueGenerator(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.generator_registry = defaultdict(list)
        self.listeners_registered = False

    def generator_wrapper(self, func, attr):
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        if isinstance(attr, six.string_types) and '.' in attr:
            parts = attr.split('.')
            self.generator_registry[parts[0]].append(wrapper)
            wrapper.__generates__ = parts[1]
        elif isinstance(attr, sa.orm.attributes.InstrumentedAttribute):
            self.generator_registry[attr.class_.__name__].append(wrapper)
            wrapper.__generates__ = attr
        else:
            wrapper.__generates__ = attr
        return wrapper

    def register_listeners(self):
        if not self.listeners_registered:
            sa.event.listen(
                sa.orm.mapper,
                'mapper_configured',
                self.update_generator_registry
            )
            sa.event.listen(
                sa.orm.session.Session,
                'before_flush',
                self.update_generated_properties
            )
            self.listeners_registered = True

    def update_generator_registry(self, mapper, class_):
        for value in class_.__dict__.values():
            if hasattr(value, '__generates__'):
                self.generator_registry[class_.__name__].append(value)

    def update_generated_properties(self, session, ctx, instances):
        for obj in itertools.chain(session.new, session.dirty):
            class_ = obj.__class__.__name__
            if class_ in self.generator_registry:
                for func in self.generator_registry[class_]:
                    attr = func.__generates__
                    if not isinstance(attr, six.string_types):
                        attr = attr.name
                    setattr(obj, attr, func(obj))


generator = AttributeValueGenerator()


def generates(attr, generator=generator):
    """
    Many times you may have generated property values. Usual cases include
    slugs from names or resized thumbnails from images.

    SQLAlchemy-Utils provides a way to do this easily with `generates`
    decorator:

    ::


        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            slug = sa.Column(sa.Unicode(255))

            @generates(slug)
            def _create_slug(self):
                return self.name.lower().replace(' ', '-')


        article = self.Article()
        article.name = u'some article name'
        self.session.add(article)
        self.session.flush()
        assert article.slug == u'some-article-name'


    You can also pass the attribute name as a string argument for `generates`:

    ::

        class Article(self.Base):
            ...

            @generates('slug')
            def _create_slug(self):
                return self.name.lower().replace(' ', '-')


    These property generators can even be defined outside classes:

    ::


        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            slug = sa.Column(sa.Unicode(255))


        @generates(Article.slug)
        def _create_article_slug(article):
            return article.name.lower().replace(' ', '-')


    Or with lazy evaluated string argument:

    ::


        @generates('Article.slug')
        def _create_article_slug(article):
            return article.name.lower().replace(' ', '-')
    """

    generator.register_listeners()

    def wraps(func):
        return generator.generator_wrapper(func, attr)
    return wraps
