__author__ = 'nati'


def rgetattr(obj, name, default=None):
    """
    recursive getattr() implementation
    """
    assert isinstance(name, basestring)
    lname, _, rname = name.partition('.')
    try:
        if rname:
            return rgetattr(getattr(obj, lname), rname, default)
        else:
            return getattr(obj, lname, default)
    except AttributeError as e:
        if default is None:
            raise e
        else:
            return default


def rget(d, key, default=None):
    """
    recursive dict.get() implementation
    """
    assert isinstance(key, basestring)
    lkey, _, rkey = key.partition('.')
    if isinstance(d, dict):
        if rkey:
            return rget(d.get(lkey), rkey, default)
        else:
            return d.get(lkey, default)
    else:
        return default


def squash_list(l):
    ret = []
    for e in l:
        ret.extend(squash_list(e) if isinstance(e, list) else [e])
    return ret
