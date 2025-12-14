from rest_framework import serializers

class QuerySerializer(serializers.Serializer):
    question = serializers.CharField(max_length=1000)

class ResponseSerializer(serializers.Serializer):
    question = serializers.CharField()
    answer = serializers.CharField()
    sources = serializers.ListField(child=serializers.CharField())
    context_used = serializers.CharField()