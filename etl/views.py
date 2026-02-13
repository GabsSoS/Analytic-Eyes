from rest_framework import generics
from etl.serializers import ETLSerializers
from etl.models import ETL

# ================================================== #
'''
    As rotas abaixo servem para lista/editar/criar/excluir ETLs
    Abaixo desse bloco se encontra as rotas que adicionam e editam o scripts de ETLS 
    nos containers Dockers

'''

class ETLsListAPIView(generics.ListCreateAPIView):
    queryset = ETL.objects.all()
    serializer_class = ETLSerializers

class ETLRetriveDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ETL.objects.all()
    serializer_class = ETLSerializers

# ================================================== #

