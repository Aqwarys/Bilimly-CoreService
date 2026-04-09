from rest_framework import serializers

from .models import Question, Quiz
from .services import validate_quiz_data


class QuestionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Question
        fields = [
            "id",
            "type",
            "content",
            "image",
            "options",
            "correct",
            "score",
            "explanation",
        ]

    def validate_options(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Options must be a list.")
        if len(value) > 15:
            raise serializers.ValidationError("Options length must be less than or equal to 15.")
        return value

    def validate(self, attrs):
        options = attrs.get("options", getattr(self.instance, "options", []))
        correct = attrs.get("correct", getattr(self.instance, "correct", []))
        q_type = attrs.get("type", getattr(self.instance, "type", None))

        if not isinstance(correct, list):
            raise serializers.ValidationError({"correct": "Correct must be a list of indexes."})
        if not all(isinstance(i, int) for i in correct):
            raise serializers.ValidationError({"correct": "All correct indexes must be integers."})
        if any(i < 0 or i >= len(options) for i in correct):
            raise serializers.ValidationError({"correct": "Correct indexes must exist in options."})

        if q_type == Question.QuestionType.SINGLE and len(correct) != 1:
            raise serializers.ValidationError(
                {"correct": "Single question must contain exactly one correct index."}
            )
        if q_type == Question.QuestionType.MULTIPLE and len(correct) < 1:
            raise serializers.ValidationError(
                {"correct": "Multiple question must contain at least one correct index."}
            )
        if q_type == Question.QuestionType.ORDERING:
            expected = list(range(len(options)))
            if correct != expected:
                raise serializers.ValidationError(
                    {
                        "correct": (
                            "Ordering question must contain the full ordered list of "
                            "option indexes starting from 0."
                        )
                    }
                )
        return attrs


class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = [
            "id",
            "course",
            "lesson",
            "title",
            "description",
            "is_free",
            "cost",
            "image",
        ]

    def validate(self, attrs):
        merged = {
            "course": attrs.get("course", getattr(self.instance, "course", None)),
            "lesson": attrs.get("lesson", getattr(self.instance, "lesson", None)),
            "is_free": attrs.get("is_free", getattr(self.instance, "is_free", True)),
            "cost": attrs.get("cost", getattr(self.instance, "cost", None)),
        }
        validate_quiz_data(merged)
        return attrs


class QuestionPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "type", "content", "image", "options", "score"]


class QuizDetailSerializer(serializers.ModelSerializer):
    questions = QuestionPublicSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "course",
            "lesson",
            "title",
            "description",
            "is_free",
            "cost",
            "image",
            "questions",
        ]


class QuizEditSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "course",
            "lesson",
            "title",
            "description",
            "is_free",
            "cost",
            "image",
            "questions",
        ]

    def validate(self, attrs):
        merged = {
            "course": attrs.get("course", getattr(self.instance, "course", None)),
            "lesson": attrs.get("lesson", getattr(self.instance, "lesson", None)),
            "is_free": attrs.get("is_free", getattr(self.instance, "is_free", True)),
            "cost": attrs.get("cost", getattr(self.instance, "cost", None)),
        }
        validate_quiz_data(merged)
        return attrs


class QuizAnswerItemSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)


class QuizCheckSerializer(serializers.Serializer):
    answers = QuizAnswerItemSerializer(many=True)


class QuizCheckResultSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    is_correct = serializers.BooleanField()
    score = serializers.IntegerField()
    explanation = serializers.CharField()
    correct_answer = serializers.ListField(child=serializers.IntegerField())


class QuestionCRUDSerializer(serializers.ModelSerializer):
    quiz = serializers.PrimaryKeyRelatedField(queryset=Quiz.objects.all())

    class Meta:
        model = Question
        fields = [
            "id",
            "quiz",
            "type",
            "content",
            "image",
            "options",
            "correct",
            "score",
            "explanation",
        ]

    def validate(self, attrs):
        options = attrs.get("options", getattr(self.instance, "options", []))
        correct = attrs.get("correct", getattr(self.instance, "correct", []))
        q_type = attrs.get("type", getattr(self.instance, "type", None))

        if not isinstance(options, list):
            raise serializers.ValidationError({"options": "Options must be a list."})
        if len(options) > 15:
            raise serializers.ValidationError({"options": "Options length must be less than or equal to 15."})

        if not isinstance(correct, list) or not all(isinstance(i, int) for i in correct):
            raise serializers.ValidationError({"correct": "Correct must be a list of integer indexes."})
        if any(i < 0 or i >= len(options) for i in correct):
            raise serializers.ValidationError({"correct": "Correct indexes must exist in options."})

        if q_type == Question.QuestionType.SINGLE and len(correct) != 1:
            raise serializers.ValidationError({"correct": "Single question must have exactly one correct index."})
        if q_type == Question.QuestionType.MULTIPLE and len(correct) < 1:
            raise serializers.ValidationError({"correct": "Multiple question must have at least one correct index."})
        if q_type == Question.QuestionType.ORDERING and correct != list(range(len(options))):
            raise serializers.ValidationError(
                {"correct": "Ordering question must contain all option indexes in exact order."}
            )

        return attrs


class QuestionBulkCreateSerializer(serializers.Serializer):
    quiz_id = serializers.PrimaryKeyRelatedField(source="quiz", queryset=Quiz.objects.all())
    questions = QuestionSerializer(many=True)


class QuestionFilterSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField(required=False)
    type = serializers.ChoiceField(choices=Question.QuestionType.choices, required=False)
    min_score = serializers.IntegerField(required=False, min_value=1, max_value=5)
    max_score = serializers.IntegerField(required=False, min_value=1, max_value=5)

    def validate(self, attrs):
        min_score = attrs.get("min_score")
        max_score = attrs.get("max_score")
        if min_score is not None and max_score is not None and min_score > max_score:
            raise serializers.ValidationError({"max_score": "max_score must be greater than or equal to min_score."})
        return attrs
