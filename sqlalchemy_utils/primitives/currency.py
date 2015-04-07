# -*- coding: utf-8 -*-
import six
from babel.numbers import get_currency_symbol

from sqlalchemy_utils import i18n
from sqlalchemy_utils.utils import str_coercible


@str_coercible
class Currency(object):
    def __init__(self, code):
        if isinstance(code, Currency):
            self.code = code
        elif isinstance(code, six.string_types):
            self.validate(code)
            self.code = code
        else:
            raise TypeError(
                'First argument given to Currency constructor should be '
                'either an instance of Currency or valid three letter '
                'currency code.'
            )

    @classmethod
    def validate(self, code):
        try:
            i18n.get_locale().currencies[code]
        except KeyError:
            raise ValueError("{0}' is not valid currency code.")

    @property
    def symbol(self):
        return get_currency_symbol(self.code, i18n.get_locale())

    @property
    def name(self):
        return i18n.get_locale().currencies[self.code]

    def __eq__(self, other):
        if isinstance(other, Currency):
            return self.code == other.code
        elif isinstance(other, six.string_types):
            return self.code == other
        else:
            return NotImplemented

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.code)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.code)

    def __unicode__(self):
        return self.name
