from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    )

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from django.contrib.auth import get_user_model
from .serializers import (
    CustomUserSerializer
)
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from tasks.tasks import send_email_task
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode




class UserViewSet(viewsets.GenericViewSet):

    permission_classes = [AllowAny]
    queryset = get_user_model().objects.all()
    serializer_class = CustomUserSerializer

    @action(methods=['POST'] , detail=False)
    def sign_up(self, request ):
        serializer = CustomUserSerializer(data = request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                data = {
                    'message':'user created'
                }
                user_data={
                    'user_name':user.user_name,
                    'first_name':user.first_name,
                    'email':user.email,
                    'pk':user.pk
                }
                send_email_task.delay(user_data)
                return Response(data=data , status=status.HTTP_201_CREATED)
        return  Response(serializer.errors , status=status.HTTP_400_BAD_REQUEST) 

    
    @action(methods=['POST'] , detail=False)
    def log_out(self,request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class VerfiyUserView(generics.GenericAPIView):
    permission_classes=[AllowAny]
    def post(self , request , uid):
        userid = force_text(urlsafe_base64_decode(uid))
        
        user = get_user_model().objects.get(pk=userid)
        if user:
            user.is_active = True
            user.save()
            message = {
                'state': 'activated'
            }
            return Response(data=message , status=status.HTTP_202_ACCEPTED)
        else:
            message = {
                'state' : 'not a valid user'
            }
            return Response(data=message , status=status.HTTP_400_BAD_REQUEST)