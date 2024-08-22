from rest_framework import serializers

from mathefragen.apps.vote.models import Vote


class VoteSerializer(serializers.ModelSerializer):

    def save(self, **kwargs):
        return Vote.create_vote(**self.validated_data)

    class Meta:
        model = Vote
        fields = (
            '__all__'
        )
