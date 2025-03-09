from rest_framework import serializers

from .models import BiasedContent


class BiasedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiasedContent
        fields = [
            "content",
            "timestamp",
            "accuracy",
            "bias_strength",
        ]


class BiasedMediaSerializer(serializers.ModelSerializer):
    biased_content = BiasedContentSerializer(many=True)

    class Meta:
        model = BiasedContent
        fields = ["name", "url", "complete", "biased_content"]
