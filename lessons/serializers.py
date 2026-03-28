"""
Serializers module for lessons app.

Contains serializers for Lesson and LessonImage models.
"""
from rest_framework import serializers
from .models import Lesson, LessonImage


class LessonCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating draft lessons.

    Only requires course_id, creates an empty draft lesson.
    """

    course_id = serializers.IntegerField(
        write_only=True,
        help_text="ID of the course this lesson belongs to."
    )

    class Meta:
        model = Lesson
        fields = ['id', 'course_id', 'is_draft']
        read_only_fields = ['id', 'is_draft']

    def validate_course_id(self, value):
        """
        Validate that the course exists.
        """
        from courses.models import Course
        try:
            course = Course.objects.get(pk=value)
            return course
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course with this ID does not exist.")

    def create(self, validated_data):
        """
        Create a new draft lesson.
        """
        course = validated_data.pop('course_id')
        lesson = Lesson(
            course=course,
            title=f"New Lesson {Lesson.objects.filter(course=course).count() + 1}",
            content={},
            is_draft=True
        )
        lesson.save()  # This will trigger the model's save method which handles priority auto-increment
        return lesson


class LessonSerializer(serializers.ModelSerializer):
    """
    Serializer for lesson details.

    Used for retrieving lesson information.
    """

    course_name = serializers.CharField(
        source='course.name',
        read_only=True,
        help_text="Name of the course this lesson belongs to."
    )

    class Meta:
        model = Lesson
        fields = [
            'id',
            'course',
            'course_name',
            'title',
            'content',
            'image',
            'is_draft',
            'auto_test',
            'priority'
        ]
        read_only_fields = ['id', 'course_name']


class LessonImageSerializer(serializers.ModelSerializer):
    """
    Serializer for lesson images.

    Used for uploading and retrieving lesson images.
    """

    class Meta:
        model = LessonImage
        fields = ['id', 'lesson', 'image']
        read_only_fields = ['id']
