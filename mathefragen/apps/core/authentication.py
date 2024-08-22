from mathefragen.apps.user.api.serializers import UserSerializer


def custom_jwt_payload_get_user_id_handler(payload):
    return payload.get('user_id')


def custom_jwt_payload_get_username_handler(payload):
    return payload.get('username')


def custom_jwt_response_payload_handler(token, user=None, request=None):
    return {
        'token': token,
        'user': UserSerializer(user, context={'request': request}).data
    }

