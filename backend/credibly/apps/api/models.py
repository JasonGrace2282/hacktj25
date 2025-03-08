from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class BiasedMedia(models.Model):
    name = models.CharField(max_length=255, unique=True)


class BiasedContent(models.Model):
    media = models.ForeignKey(
        BiasedMedia,
        related_name="biased_content",
        on_delete=models.CASCADE,
    )

    content = models.TextField()
    timestamp = models.DurationField(verbose_name="Video timestamp", null=True)

    accuracy = models.FloatField(
        help_text="A value between 0 and 1 representing how truthful the information is",
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        null=True,
    )

    bias_strength = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
