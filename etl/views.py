from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from etl.serializers import ETLSerializers
from etl.models import ETL

# listagem de ETLS
class ETLsListAPIView(generics.ListAPIView):
    queryset = ETL.objects.all()
    serializer_class = ETLSerializers

    


