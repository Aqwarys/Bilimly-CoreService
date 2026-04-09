from rest_framework import serializers

from .models import Question, Quiz


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
        instance = getattr(self, "instance", None)
        course = attrs.get("course", getattr(instance, "course", None))
        lesson = attrs.get("lesson", getattr(instance, "lesson", None))
        is_free = attrs.get("is_free", getattr(instance, "is_free", True))
        cost = attrs.get("cost", getattr(instance, "cost", None))

        if bool(course) == bool(lesson):
            raise serializers.ValidationError("Exactly one of course or lesson must be set.")

        if not is_free and cost is None:
            raise serializers.ValidationError({"cost": "Cost is required when quiz is not free."})

        return attrs


class QuestionSerializer(serializers.ModelSerializer):
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
        instance = getattr(self, "instance", None)
        question_type = attrs.get("type", getattr(instance, "type", None))
        options = attrs.get("options", getattr(instance, "options", []))
        correct = attrs.get("correct", getattr(instance, "correct", []))
        score = attrs.get("score", getattr(instance, "score", 1))

        if not isinstance(options, list):
            raise serializers.ValidationError({"options": "Options must be a list."})

        if len(options) > 15:
            raise serializers.ValidationError({"options": "Options length must be less than or equal to 15."})

        if not isinstance(correct, list):
            raise serializers.ValidationError({"correct": "Correct must be a list of indexes."})

        if any(not isinstance(index, int) for index in correct):
            raise serializers.ValidationError({"correct": "Correct indexes must be integers."})

        if any(index < 0 or index >= len(options) for index in correct):
            raise serializers.ValidationError({"correct": "Correct indexes must reference existing options."})

        if score < 1 or score > 5:
            raise serializers.ValidationError({"score": "Score must be between 1 and 5."})

        if question_type == Question.TYPE_SINGLE and len(correct) != 1:
            raise serializers.ValidationError({"correct": "Single type must contain exactly one correct index."})

        if question_type == Question.TYPE_MULTIPLE and len(correct) < 1:
            raise serializers.ValidationError({"correct": "Multiple type must contain at least one correct index."})

        if question_type == Question.TYPE_ORDERING:
            expected = list(range(len(options)))
            if sorted(correct) != expected or len(correct) != len(options):
                raise serializers.ValidationError(
                    {"correct": "Ordering type requires full order of all option indexes."}
                )

        return attrs


class QuestionPassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            "id",
            "type",
            "content",
            "image",
            "options",
            "score",
        ]


class QuizPassSerializer(serializers.ModelSerializer):
    questions = QuestionPassSerializer(many=True, read_only=True)

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


class QuestionEditSerializer(serializers.ModelSerializer):
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


class QuizEditSerializer(serializers.ModelSerializer):
    questions = QuestionEditSerializer(many=True, read_only=True)

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


class FullQuizQuestionUpdateSerializer(QuestionSerializer):
    id = serializers.IntegerField(required=False)
    quiz = serializers.IntegerField(required=False)


class FullQuizUpdateSerializer(QuizSerializer):
    questions = FullQuizQuestionUpdateSerializer(many=True)

    class Meta(QuizSerializer.Meta):
        fields = QuizSerializer.Meta.fields + ["questions"]


class QuizAnswerItemSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)


class QuizCheckRequestSerializer(serializers.Serializer):
    answers = QuizAnswerItemSerializer(many=True)


class QuizCheckResultSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    is_correct = serializers.BooleanField()
    score = serializers.IntegerField()
    explanation = serializers.CharField()
    correct_answer = serializers.ListField(child=serializers.IntegerField())