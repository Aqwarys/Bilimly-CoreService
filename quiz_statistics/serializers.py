from rest_framework import serializers

from .models import UserAnswer, UserAttempt


class UserAnswerSerializer(serializers.ModelSerializer):
    question_id = serializers.IntegerField(source="question.id", read_only=True)
    selected = serializers.ListField(source="selected_options", child=serializers.IntegerField(), read_only=True)
    correct_answer = serializers.ListField(source="question.correct", child=serializers.IntegerField(), read_only=True)

    class Meta:
        model = UserAnswer
        fields = ["question_id", "selected", "is_correct", "correct_answer"]


class UserAttemptSerializer(serializers.ModelSerializer):
    answers = UserAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = UserAttempt
        fields = ["id", "quiz", "score", "is_completed", "created_at", "updated_at", "answers"]


class UserStatisticsSerializer(serializers.Serializer):
    total_score = serializers.IntegerField()
    total_quizzes_passed = serializers.IntegerField()
    attempts = UserAttemptSerializer(many=True)
