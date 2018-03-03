import random


class QueryAuthMiddleware:
    """
    Middleware that takes JWTs from the query string.
    """

    def __init__(self, inner):
        self.inner = inner

    # DIFFERENCE: in the real app we parse a JWT here
    def __call__(self, scope):
        customer_identifier = random.choice('12345')
        staff_key = customer_identifier + random.choice('abcde')

        scope['user'] = {'staff_key': staff_key, 'customer_identifier': customer_identifier}

        return self.inner(scope)
