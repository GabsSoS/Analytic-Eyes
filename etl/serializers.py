from rest_framework import serializers
from etl.models import ETL
from django.contrib.auth.models import User

class ETLSerializers(serializers.ModelSerializer):
    class Meta:
        model = ETL
        fields = ['title', 'status', 'owner']
        
