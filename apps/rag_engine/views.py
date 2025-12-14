from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import QuerySerializer, ResponseSerializer
from .logic.hybrid_search import HybridRAGEngine

class AskView(APIView):
    def post(self, request):
        serializer = QuerySerializer(data=request.data)
        if serializer.is_valid():
            question = serializer.validated_data['question']
            
            engine = HybridRAGEngine()
            result = engine.answer_question(question)
            
            response_serializer = ResponseSerializer(result)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)