from rest_framework import serializers
from .models import Category, Course
from lessons.models import Lesson
from lessons.serializers import LessonSerializer as BaseLessonSerializer


class CourseShortSerializer(serializers.ModelSerializer):
    """
    Short serializer for Course, used in CategorySerializer.
    """

    slug = serializers.SlugField(help_text="Unique slug used in course URLs")
    name = serializers.CharField(help_text="Course title displayed to users")
    description = serializers.CharField(help_text="Course description")
    image = serializers.ImageField(help_text="Course image", required=False)
    is_free = serializers.BooleanField(help_text="Indicates whether the course is free or requires subscription")
    cost = serializers.DecimalField(
        max_digits=10, decimal_places=2, help_text="Course price. Only used if course is paid", required=False, allow_null=True
    )

    class Meta:
        model = Course
        fields = ["slug", "name", "description", "image", "is_free", "cost"]


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category with nested courses.
    """

    code = serializers.CharField(help_text="Category code")
    name = serializers.CharField(help_text="Category name")
    description = serializers.CharField(help_text="Category description")
    image = serializers.ImageField(help_text="Category image", required=False)
    courses = CourseShortSerializer(many=True, read_only=True, help_text="List of courses in this category")

    class Meta:
        model = Category
        fields = ["code", "name", "description", "image", "courses"]


class CourseDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Course.
    """

    category = serializers.StringRelatedField(help_text="Category name")
    slug = serializers.SlugField(help_text="Unique slug used in course URLs")
    name = serializers.CharField(help_text="Course title displayed to users")
    description = serializers.CharField(help_text="Course description")
    image = serializers.ImageField(help_text="Course image", required=False)
    is_free = serializers.BooleanField(help_text="Indicates whether the course is free or requires subscription")
    cost = serializers.DecimalField(
        max_digits=10, decimal_places=2, help_text="Course price. Only used if course is paid", required=False, allow_null=True
    )

    class Meta:
        model = Course
        fields = ["category", "name", "slug", "description", "image", "is_free", "cost"]
