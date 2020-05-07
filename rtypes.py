import types
import inspect
from typing import *

BUILTIN_TYPES = [int, float, str, bytes]
TYPE_MAP = []

def typeify_function(f):
    if not hasattr(f, "__annotations__"):
        return Callable

    rettype = f.__annotations__.get("return", Any)
    argtypes = {k: v for k, v in f.__annotations__.items()}
    args = inspect.getfullargspec(f).args
    if "return" in argtypes:
        argtypes.pop("return")
    argtypes2 = []
    for i in args:
        if i in argtypes:
            argtypes2.append(argtypes[i])
        else:
            argtypes2.append(Any)
    return Callable[argtypes2, rettype]
    
def verify_type(name, x, t):
    if t == Any:
        return
    if get_origin(t) == Union:
        for i in t.__args__:
            try:
                verify_type(name, x, i)
                return
            except TypeError:
                pass
        args = ",".join(str(i) for i in t.__args__[:-1]) + " or " + str(t.__args__[-1])
        raise TypeError("%sExpected %s, got %s" % ("Field "+name+": " if name else "", args, type(x).__name__))
    if t in BUILTIN_TYPES or type(x) in BUILTIN_TYPES:
        if t == type(x):
            return
        if type(t) == type:
            raise TypeError("%sExpected %s, got %s" % ("Field "+name+": " if name else "", t.__name__, type(x).__name__))
        else:
            raise TypeError("%sExpected %s, got %s" % ("Field "+name+": " if name else "", t, type(x).__name__))
    if type(t) == type:
        # is a class
        if issubclass(t, TypedObject):
            # Polymorphism
            if issubclass(type(x), t):
                return
            raise TypeError("%s'%s' does not extend '%s'" % (type(x), t))
    if type(x) in TYPE_MAP:
        typeified = x.typeify()
        if typeified == t:
            return
        if hasattr(t, "__args__"):
            f = True
            for i in t.__args__:
                if type(i) != TypeVar:
                    f = False
            if f:
                if get_origin(typeified) == get_origin(t):
                    return
        raise TypeError("%sExpected %s, got %s" % ("Field "+name+": " if name else "", typeified, t))
    if type(x) in TYPE2TYPEIFY_MAP:
        typeified = TYPE2TYPEIFY_MAP[type(x)](x)
        if typeified == t:
            return
        if hasattr(t, "__args__"):
            f = True
            for i in t.__args__:
                if type(i) != TypeVar:
                    f = False
            if f:
                if get_origin(typeified) == get_origin(t):
                    return
        raise TypeError("%sExpected %s, got %s" % ("Field "+name+": " if name else "", typeified, t))
    raise TypeError("%sPython type '%s' doesn't fulfil any typing type" % ("Field "+name+": " if name else "", type(x).__name__))

class TypedObject():

    __dict__: Any
    __class__: Any

    weak_typing = False

    def __getattribute__(self, x):
        f = object.__getattribute__(self, "__class__").__annotations__
        weak_typing = object.__getattribute__(self, "__class__").weak_typing
        xval = object.__getattribute__(self, x)

        if x in f:
            verify_type(x, xval, f[x])
            return xval
        if weak_typing:
            return xval
        raise TypeError("Field '%s' doesn't have a type." % x)

    def __setattr__(self, x, y):
        f = object.__getattribute__(self, "__class__").__annotations__
        weak_typing = object.__getattribute__(self, "__class__").weak_typing

        if x in f:
            verify_type(x, y, f[x])
            object.__setattr__(self, x, y)
            return
        if weak_typing:
            object.__setattr__(self, x, y)
            return
        raise TypeError("Field '%s' doesn't have a type." % x)


def fulfils_type(c):
    TYPE_MAP.append(c)
    return c

TYPE2TYPEIFY_MAP = {
    types.FunctionType: typeify_function,
    types.MethodType:   typeify_function
    # types.LambdaType:   (lambda x: Callable)
}

@fulfils_type
class ListType():

    def typeify(self):
        return List[self.type]

    def __init__(self, t, obj=None):
        if obj == None:
            obj = []
        self.type = t
        self._list = obj

    def append(self, obj):
        verify_type(None, obj, self.type)
        self._list.append(obj)

    def extend(self, obj):
        verify_type(None, obj, self.type)
        self._list.extend(obj)

    def __getitem__(self, x):
        return self._list[x]

    def __setitem__(self, x, y):
        verify_type(None, y, self.type)
        self._list[x] = y

    def __delitem__(self, x):
        del self._list[x]

    def __iter__(self):
        return iter(self._list)

    def __repr__(self):
        return repr(self._list)

    def __str__(self):
        return str(self._list)

@fulfils_type
class DictType():

    def typeify(self):
        return List[Tuple[self.keytype, self.valtype]]

    def __init__(self, keytype, valtype, obj=None):
        self.keytype = keytype
        self.valtype = valtype
        self.obj = obj
        if self.obj == None: self.obj = {}

    def __getitem__(self, x):
        verify_type(None, x, self.keytype)
        return self.obj[x]

    def __setitem__(self, x, y):
        verify_type(None, x, self.keytype)
        verify_type(None, y, self.valtype)
        self.obj[x] = y

    def __iter__(self):
        for i in self.obj:
            yield self[i]

    def __repr__(self):
        return repr(self.obj)

    def __str__(self):
        return repr(self.obj)

    def update(self, other):
        verify_type(None, other, DictType)
        for i in other:
            self[i] = other[i]
