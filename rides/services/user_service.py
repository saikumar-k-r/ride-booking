from django.contrib.auth import get_user_model

User = get_user_model()


def get_user_by_id(user_id):
    return User.objects.get(id=user_id)


def create_user(**validated_data):
    return User.objects.create_user(**validated_data)