from ipware import get_client_ip


class IP:

    def __init__(self, request):
        self.request = request

    def user_ip(self):
        return self._get_ip()

    def _get_ip(self):
        client_ip, is_routable = get_client_ip(self.request)
        if client_ip is None:
            # Unable to get the client's IP address
            return
        else:
            # We got the client's IP address
            if is_routable:
                # The client's IP address is publicly routable on the Internet
                return client_ip
            else:
                # The client's IP address is private
                return
