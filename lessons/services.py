"""
Services module for lessons app.

Contains business logic functions that can be reused across views.
"""


def cleanup_unused_images(lesson):
    """
    Remove unused LessonImage records for a lesson.

    Compares images in Lesson.content with LessonImage records
    and deletes any LessonImage records that are not referenced
    in the content.

    Args:
        lesson (Lesson): The lesson instance to clean up images for.

    Returns:
        int: Number of images deleted.
    """
    from django.core.files.storage import default_storage

    # Get all image URLs referenced in the lesson content
    used_image_urls = set()

    if lesson.content:
        # Extract image URLs from TipTap JSON content
        # TipTap stores images as nodes with type "image" and src attribute
        used_image_urls = _extract_image_urls_from_content(lesson.content)

    # Get all LessonImage records for this lesson
    existing_images = lesson.images.all()

    deleted_count = 0

    # Delete LessonImage records that are not referenced in content
    for lesson_image in existing_images:
        # Construct the URL that would be used in content
        image_url = lesson_image.image.url

        if image_url not in used_image_urls:
            # Delete the file from storage
            if default_storage.exists(lesson_image.image.name):
                default_storage.delete(lesson_image.image.name)

            # Delete the LessonImage record
            lesson_image.delete()
            deleted_count += 1

    return deleted_count


def _extract_image_urls_from_content(content):
    """
    Extract image URLs from TipTap editor JSON content.

    TipTap stores images as nodes with type "image" and src attribute.
    This function recursively traverses the JSON structure to find all image URLs.

    Args:
        content (dict): TipTap editor content in JSON format.

    Returns:
        set: Set of image URLs found in the content.
    """
    image_urls = set()

    def traverse_node(node):
        if isinstance(node, dict):
            # Check if this is an image node
            if node.get('type') == 'image' and 'attrs' in node:
                src = node['attrs'].get('src')
                if src:
                    image_urls.add(src)

            # Recursively traverse children
            for key, value in node.items():
                if key != 'attrs':  # Skip attrs as we've already processed it
                    traverse_node(value)

        elif isinstance(node, list):
            # Traverse array items
            for item in node:
                traverse_node(item)

    # Start traversal from the root content
    if isinstance(content, dict) and 'content' in content:
        traverse_node(content['content'])
    elif isinstance(content, list):
        for item in content:
            traverse_node(item)

    return image_urls