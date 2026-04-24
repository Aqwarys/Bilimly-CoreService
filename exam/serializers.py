from rest_framework import serializers

from .models import Module, Problem, Subject


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "type",
            "duration_sec",
            "max_score",
        ]


class SubjectGroupedSerializer(serializers.Serializer):
    type = serializers.CharField()
    subjects = SubjectSerializer(many=True)


class ProblemPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = [
            "id",
            "type",
            "content",
            "image",
            "audio",
            "options",
        ]


class ExamSubjectSerializer(serializers.Serializer):
    name = serializers.CharField()
    total_problem = serializers.IntegerField()
    max_score = serializers.IntegerField()
    problems = ProblemPublicSerializer(many=True)


class ExamResponseSerializer(serializers.Serializer):
    total_duration_sec = serializers.IntegerField()
    total_problem_count = serializers.IntegerField()
    total_score_sum = serializers.IntegerField()
    subjects = ExamSubjectSerializer(many=True)


class ExamCheckProblemInputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    selected = serializers.ListField(
        child=serializers.IntegerField(), allow_null=True, required=False
    )


class ExamCheckSubjectInputSerializer(serializers.Serializer):
    name = serializers.CharField()
    problems = ExamCheckProblemInputSerializer(many=True)


class ExamCheckProblemResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    correct = serializers.ListField(child=serializers.IntegerField())
    selected = serializers.ListField(child=serializers.IntegerField(), allow_null=True)
    explanation = serializers.CharField()
    is_correct = serializers.BooleanField()


class ExamCheckSubjectResultSerializer(serializers.Serializer):
    name = serializers.CharField()
    total_score_get = serializers.IntegerField()
    problems = ExamCheckProblemResultSerializer(many=True)


class ExamCheckResponseSerializer(serializers.Serializer):
    total_get_score = serializers.IntegerField()
    total_score_sum = serializers.IntegerField()
    subjects = ExamCheckSubjectResultSerializer(many=True)
