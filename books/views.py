from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated  
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import Book, Author, Vendor, Genre, BookEditions
from iam.permissions import IsAdminUser,IsSuperAdminUser, IsVendorUser
from rest_framework.permissions import IsAuthenticated 
from .serializers import AuthorSerializer
from iam.models import CustomUser, profile

import logging

logger = logging.getLogger(__name__)


# Create your views here.

class AuthorView(APIView):
    permission_classes = [IsAdminUser]
    def post(self, request, *args, **kwargs):
        try:
            author = request.data.get('author')
            logger.debug("Received author ID: %s", author)
            author_object = CustomUser.objects.get(id=author, is_active=True)
            logger.debug("Author object retrieved: %s", author_object)

            if not author_object:
                return Response({"error": "Author not found or inactive"}, status=status.HTTP_404_NOT_FOUND)
            serializer = AuthorSerializer(data=request.data, context ={'author': author_object})
            if serializer.is_valid():
                logger.debug("Author serializer is valid: %s", serializer.validated_data)
                author_profile = serializer.save()
                return Response({"message": "Author profile created successfully", "author_id": author_profile.id}, status=status.HTTP_201_CREATED)
        except CustomUser.DoesNotExist:
            logger.error("Author with ID %s does not exist", author)
            return Response({"error": "Author does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("Error creating author profile: %s", str(e))
            return Response({"error": "An error occurred while creating the author profile"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AuthorListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            authors = Author.objects.all()
            logger.debug("Retrieved authors: %s", authors)

            authors_list = []
            for book_author in authors:
                logger.debug("Processing author: %s", book_author.author_id)
                
                author_object = CustomUser.objects.select_related("profile","author_profile").get(id=book_author.author_id, is_active=True)
                logger.debug("Processing author object: %s", author_object)
                data = {
                    #"id": author_object.id,
                    "first_name": author_object.first_name,
                    "last_name": author_object.last_name,
                    "email": author_object.email,
                    "is_active": author_object.is_active,
                    "profile": {
                        "bio": author_object.Author.bio if hasattr(author_object, 'Author') else None,
                        "phone_number": author_object.profile.phone_number if hasattr(author_object, 'profile') else None,
                        "D_no": author_object.profile.D_no if hasattr(author_object, 'profile') else None,
                        "street_name": author_object.profile.street_name if hasattr(author_object, 'profile') else None,
                        "city": author_object.profile.city if hasattr(author_object, 'profile') else None,
                        "state": author_object.profile.state if hasattr(author_object, 'profile') else None,
                        "country": author_object.profile.country if hasattr(author_object, 'profile') else None,
                        "zip_code": author_object.profile.zip_code if hasattr(author_object, 'profile') else None
                    }
                    
                } 
                logger.debug("Author data: %s", data)
                authors_list.append(data)
            return Response({"data" : authors_list},status=status.HTTP_200_OK)
        
        except CustomUser.DoesNotExist:
            logger.error("No active authors found")
            return Response({"error": "No active authors found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("Error retrieving authors: %s", str(e))
            return Response({"error": "An error occurred while retrieving authors"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)