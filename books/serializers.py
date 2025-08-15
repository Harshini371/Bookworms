from rest_framework import serializers
from .models import Book, Author
from iam.models import CustomUser, profile
import logging
logger = logging.getLogger(__name__)

class AuthorSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    bio = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Author
        fields = ['id', 'author', 'bio']

    def create(self, validated_data):
        logger.debug("Creating author profile with data: %s", validated_data)

        author = self.context.get('author')
        author_data = validated_data.copy()
        author_data['author'] = author
        author_instance = Author.objects.create(**author_data)
        return author_instance
        logger.debug("validated author ID: %s", validated_data)
        author_profile = Book.Author.objects.create(author=author, **validated_data)
        return author_profile


