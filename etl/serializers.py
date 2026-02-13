from rest_framework import serializers
from etl.models import ETL
from django.contrib.auth.models import User

class ETLSerializers(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ETL
        fields = "__all__"
        read_only_fields = ("id",)


