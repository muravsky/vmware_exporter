'''
Helpers for writing efficient twisted code, optimized for coroutine scheduling efficiency
'''
# autopep8'd

from twisted.internet import defer
from twisted.python import failure

_UNSET = object()


class BranchingDeferred(defer.Deferred):

    '''
    This is meant for code where you are doing something like this:

    content = yield self.get_connection_content()
    results = yield defer.DeferredList([
        self.get_hosts(content),
        self.get_datastores(content),
    ])

    This allows get_hosts and get_datastores to run in parallel, which is good.
    But what if you don't want the whole of get_hosts to wait for
    get_connection_content() to be complete?

    We have a bunch of places where it would be better for scheduling if we did this:

    content = self.get_connection_content()
    results = yield defer.DeferredList([
        self.get_hosts(content),
        self.get_datastores(content),
    ])

    Now we don't have to wait for content to be finished before get_hosts etc
    starts running. It is up to get_hosts to block on the content deferred itself.

    (Thats a contrived example, the real win is allowing host_labels and
    vm_inventory to run in parallel).

    Unfortunately you can't have parallel branches blocking on the same deferred
    like this with a standard Twisted deferred.

    This is a deferred that enables the parallel branching use case.
    '''

    def __init__(self):
        defer.Deferred.__init__(self)
        self._branch_callbacks = []
        self._branch_result = _UNSET
        self._branch_resolved = False

    @property
    def result(self):
        if self._branch_resolved:
            return self._branch_result
        return None

    @result.setter
    def result(self, value):
        # Twisted updates result while running callbacks; keep branch value stable.
        if not self._branch_resolved:
            self._branch_result = value

    def callback(self, result):
        if isinstance(result, failure.Failure):
            return self.errback(result)

        if self._branch_resolved:
            return

        self._branch_resolved = True
        self._branch_result = result
        waiters = self._branch_callbacks
        self._branch_callbacks = []
        for waiter in waiters:
            waiter.callback(result)

        defer.Deferred.callback(self, result)

    def errback(self, err):
        if not isinstance(err, failure.Failure):
            err = failure.Failure(err)

        if self._branch_resolved:
            return

        self._branch_resolved = True
        self._branch_result = err
        waiters = self._branch_callbacks
        self._branch_callbacks = []
        for waiter in waiters:
            waiter.errback(err)

        defer.Deferred.errback(self, err)

    def addCallbacks(self, callback, errback=None,
                     callbackArgs=None, callbackKeywords=None,
                     errbackArgs=None, errbackKeywords=None):
        if not self._branch_resolved:
            d = defer.Deferred()
            d.addCallbacks(
                callback,
                errback,
                callbackArgs,
                callbackKeywords,
                errbackArgs,
                errbackKeywords,
            )
            self._branch_callbacks.append(d)
            return d

        if isinstance(self._branch_result, failure.Failure):
            return defer.fail(self._branch_result).addCallbacks(
                callback,
                errback,
                callbackArgs,
                callbackKeywords,
                errbackArgs,
                errbackKeywords,
            )

        return defer.succeed(self._branch_result).addCallbacks(
            callback,
            errback,
            callbackArgs,
            callbackKeywords,
            errbackArgs,
            errbackKeywords,
        )


class run_once_property(object):

    '''
    This is a property descriptor that caches the first result it retrieves. It
    does this by setting keys in self.__dict__ on the parent class instance.
    This is fast - python won't even bother running our descriptor next time
    because attributes in self.__dict__ on a class instance trump descriptors
    on the class.

    This is intended to be used with the Collector class which has a request
    bound lifecycle (this isn't going to cache stuff forever and cause memory
    leaks).
    '''

    def __init__(self, callable):
        self.callable = callable

    def __get__(self, obj, cls):
        if obj is None:
            return self
        result = obj.__dict__[self.callable.__name__] = BranchingDeferred()
        self.callable(obj).chainDeferred(result)
        return result


@defer.inlineCallbacks
def parallelize(*args):
    results = yield defer.DeferredList(args, fireOnOneErrback=True)
    return tuple(r[1] for r in results)
