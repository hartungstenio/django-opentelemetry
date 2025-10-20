from django.db import models


class SimpleModel(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        metric_label: str = "simple_model"

    def __str__(self) -> str:
        return str(self.pk)
