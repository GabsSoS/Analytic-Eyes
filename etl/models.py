from django.db import models
from django.contrib.auth.models import User

STATUS_CHOICES = (
    ('1', 'ETL Ativa'),
    ('2', 'ETL Inativa'),
    ('3', 'ETL com Erro'),
)

PATH_CHOICES = (
    ('1', 'caminho/pasta1'),
    ('2', 'caminho/pasta2'),
    ('3', 'caminho/pasta3'),

)

class ETL(models.Model):
    owner = models.ForeignKey(
        "auth.User",
        related_name='etls',
        on_delete=models.CASCADE,
        null=False,
        blank=False,

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
    rota = models.CharField(
        max_length=1,
        choices=PATH_CHOICES,
        default='1'
    )

    