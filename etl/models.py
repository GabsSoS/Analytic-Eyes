from django.db import models
from django.contrib.auth.models import User

STATUS_CHOICES = (
    ('1', 'ETL Ativa'),
    ('2', 'ETL Inativa'),
    ('3', 'ETL com Erro'),
)

class ETL(models.Model):
    owner = models.ForeignKey(
        User,
        related_name='etl_owned',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=100, blank=True, null=True)
    create_date = models.DateField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    coowners = models.ManyToManyField(
        User,
        related_name='etl_coowned',
        blank=True
    )
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default='1'
    )

    