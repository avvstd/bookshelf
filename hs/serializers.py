from rest_framework import serializers
from main.models import Shelf, BookUser, ShelfRecord
from bookshelf.settings import MEDIA_ROOT
from base64 import b64encode
from os.path import split
import logging

logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):

    userpic = serializers.SerializerMethodField()

    class Meta:
        model = BookUser
        fields = ('id', 'username', 'is_superuser', 'first_name', 'last_name', 'email', 'sex', 'is_activated', 'userpic')

    def get_userpic(self, user):
        userpic = user.userpic
        if userpic:
            file_path = MEDIA_ROOT / userpic.name
            with open(file_path, "rb") as image_file:
                encoded_string = b64encode(image_file.read()).decode('ascii')
                filename = split(userpic.name)[1]
                data = {
                    'name': filename,
                    'data': encoded_string
                }
                return data
        else:
            return None

class ShelfSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shelf
        fields = ('id', 'name', 'private', 'owner')

class ShelfRecordSerializerGET(serializers.ModelSerializer):

    cover = serializers.SerializerMethodField()

    class Meta:
        model = ShelfRecord
        fields = ('id', 'title', 'author', 'comment', 'rating', 'read_date', 'random_cover', 'cover')

    def get_cover(self, record):
        cover = record.cover
        if cover:
            file_path = MEDIA_ROOT / cover.name
            with open(file_path, "rb") as image_file:
                file_data = b64encode(image_file.read()).decode('ascii')
            result = {
                'name': cover.name,
                'data': file_data,
            }
            return result
        else:
            return None
        
class ShelfRecordSerializerPOST(serializers.ModelSerializer):

    class Meta:
        model = ShelfRecord
        fields = '__all__'

    