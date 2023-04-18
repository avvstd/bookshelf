from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ParseError, ValidationError, APIException
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.authentication import BasicAuthentication
from django.http import JsonResponse
from django.urls import reverse
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.transaction import rollback

from random import randint
import logging, base64

from main.models import Shelf, BookUser, ShelfRecord
from .serializers import ShelfSerializer, UserSerializer, ShelfRecordSerializerGET, ShelfRecordSerializerPOST

logger = logging.getLogger(__name__)

@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAdminUser])
def users_view(request):
    if request.method == 'GET':
        users = BookUser.objects.all()
        serializer = UserSerializer(users, many=True)
        return JsonResponse(serializer.data, safe=False)

@api_view(['GET', 'POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def shelfs_view(request):
    if request.method == 'GET':
        shelfs = Shelf.objects.filter(owner=request.user)
        serializer = ShelfSerializer(shelfs, many=True)
        return JsonResponse(serializer.data, safe=False)
    elif request.method == 'POST':
        data = request.data
        data['owner'] = request.user.pk
        serializer = ShelfSerializer(data=data)
        if serializer.is_valid():
            shelf = serializer.save()
            urn = reverse('main:shelf_detail', args=(shelf.pk,))
            return JsonResponse({'urn': urn}, status=status.HTTP_201_CREATED)
        else:
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['GET', 'POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticatedOrReadOnly])
def records_view(request, shelf_pk):
    try:
        shelf = Shelf.objects.get(pk=shelf_pk)
    except Shelf.DoesNotExist:
        raise NotFound(detail='Объект не найден')
    
    if shelf.private:
        if shelf.owner != request.user:
            raise PermissionDenied(detail='У Вас нет доступа к этой полке')
        
    if request.method == 'GET':
        records = ShelfRecord.objects.filter(shelf=shelf)
        serializer = ShelfRecordSerializerGET(records, many=True)
        return JsonResponse(serializer.data, safe=False)
    elif request.method == 'POST':
        if shelf.owner != request.user:
            raise PermissionDenied(detail='У Вас нет доступа к этой полке')
        
        data = request.data

        if 'cover' in data:
            cover_meta = data['cover']
            if not ('name' in cover_meta and 'data' in cover_meta):
                raise ParseError(detail='Wrong context. Must contain both <name> and <data> fields')
            
            b_data = base64.b64decode(cover_meta['data'])
            name = cover_meta['name']
            cover = ContentFile(b_data, name=name)
            data['cover'] = cover
        
        data['random_cover'] = randint(1, 6)

        serializer = ShelfRecordSerializerPOST(data=data)
        if serializer.is_valid():
            record = serializer.save()
            urn = reverse('main:record_detail', args=(record.pk,))
            return JsonResponse({'urn': urn}, status=status.HTTP_201_CREATED)
        else:
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
@transaction.atomic
def records_add(request):

    shelfs = shelfs_processing(request)
    records = records_processing(request, shelfs)

    result = {
        'shelfs': shelfs,
        'records': records,
    }

    return JsonResponse(result, status=status.HTTP_201_CREATED)

def shelfs_processing(request):
    
    incoming_data = request.data
    shelfs = {}

    if 'shelfs' in incoming_data:
        for shelf_data in incoming_data['shelfs']:
            code = shelf_data['code']
            if not shelf_data['id']:
                creation_data = {
                    'name': shelf_data['title'],
                    'private': shelf_data['private'],
                    'owner': request.user.pk
                }
                serializer = ShelfSerializer(data=creation_data)
                if serializer.is_valid():
                    shelf = serializer.save()
                    shelfs[code] = shelf.id
                else:
                    detail = {'preamble': f'Problems with saving shelf with code {code}',}
                    detail.update(serializer.errors)
                    raise ValidationError(detail=detail)
            else:
                shelfs[code] = shelf_data['id']

    return shelfs

def records_processing(request, shelfs):

    incoming_data = request.data
    records = {}

    if 'records' in incoming_data:
        for record_data in incoming_data['records']:

            code = record_data['code']
            shelf_code = record_data['shelf_code']

            shelf_id = shelfs.get(shelf_code)

            if not shelf_id:
                detail = f'Shelf with code {shelf_code} is not found'
                raise APIException(detail=detail)
                        
            try:
                shelf = Shelf.objects.get(pk=shelf_id)
            except Shelf.DoesNotExist:
                raise NotFound(detail=f'Shelf with id {shelf_id} is not found')
            
            if shelf.owner != request.user:
                raise PermissionDenied(detail='У Вас нет доступа к этой полке')

            creation_data = {
                'title': record_data['title'],
                'author': record_data['author'],
                'rating': record_data['rating'],
                'comment': record_data['comment'],
                'shelf': shelf.pk,
                'random_cover': record_data['random_cover'],
                'read_date': record_data['read_date'],
                'cover': None,
            }

            cover_data = record_data['cover']
            if cover_data:
                if not ('name' in cover_data and 'data' in cover_data):
                    detail = f'Wrong filedata-context in record {code}. Must contain both <name> and <data> fields'
                    raise ValidationError(detail=detail)
                
                binary_data = base64.b64decode(cover_data['data'])
                name = cover_data['name']
                cover = ContentFile(binary_data, name=name)
                creation_data['cover'] = cover

            serializer = ShelfRecordSerializerPOST(data=creation_data)
            if serializer.is_valid():
                record = serializer.save()
                records[code] = record.id
            else:
                detail = {'preamble': f'Problems with saving record with code {code}',}
                detail.update(serializer.errors)
                raise ValidationError(detail=detail)
            
    return records