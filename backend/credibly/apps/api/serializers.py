from rest_framework import serializers

from .models import BiasedContent


class BiasedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiasedContent
        fields = [
            "media__name",
            "content",
            "timestamp",
            "accuracy",
            "bias_strength",
        ]
