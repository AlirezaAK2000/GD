from django.shortcuts import render
from django.http import Http404
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics, mixins, views
import user
from .models import *
from .serializers import *
from rest_framework.permissions import (
    IsAuthenticated,
    IsAdminUser,
    AllowAny
)
from rest_framework.decorators import action
from rest_framework import viewsets
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from collections import defaultdict
from .viewsets import *
from tasks.tasks import send_team_requests_task
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode

class TalkViewSet(ServicesModelViewSet):
    queryset = Talk.objects.all()
    serializer_class = TalksPageSerializer
    model = Talk
    service_type = 'TK'


class WorkshopViewSet(ServicesModelViewSet):
    queryset = Workshop.objects.all()
    serializer_class = WorkshopPageSerializer
    model = Workshop
    service_type = 'WS'


class UserServicesViewSet(ResponseGenericViewSet):
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = EventService.objects.all()
    serializer_class = EventServiceSerializer

    @action(methods=['GET'], detail=False, permission_classes=[IsAuthenticated])
    def services(self, request):
        try:
            user = request.user
            services = user.services
            data = EventServiceSerializer(services, many=True)
            return Response(data.data)
        except EventService.DoesNotExist:
            return Http404


class CompetitionMemberViewSet(ResponseGenericViewSet,
                               mixins.UpdateModelMixin,
                               mixins.DestroyModelMixin,
                               mixins.ListModelMixin,
                               mixins.RetrieveModelMixin):
    queryset = CompetitionMember.objects.all()
    serializer_class = CompetitionMemberSerializer
    permission_classes_by_action = {
        'list': [IsAuthenticated],
        'retrive': [IsAuthenticated],
        'destroy': [IsAdminUser],
        'update': [IsAdminUser],
    }

    def retrieve(self, request, *args, **kwargs):
        response_data = super(CompetitionMemberViewSet, self).retrieve(
            request, *args, **kwargs)
        self.response_format["data"] = response_data.data
        self.response_format["status"] = 200
        if not response_data.data:
            self.response_format["message"] = "Empty"
        return Response(self.response_format)

    def list(self, request, *args, **kwargs):
        response_data = super(CompetitionMemberViewSet, self).list(
            request, *args, **kwargs)
        self.response_format["data"] = response_data.data
        self.response_format["status"] = 200
        if not response_data.data:
            self.response_format["message"] = "List empty"
        return Response(self.response_format)

    def update(self, request, *args, **kwargs):
        response_data = super(CompetitionMemberViewSet, self).update(
            request, *args, **kwargs)
        self.response_format["data"] = response_data.data
        self.response_format["status"] = 200

        return Response(self.response_format)

    def destroy(self, request, *args, **kwargs):
        response_data = super(CompetitionMemberViewSet, self).destroy(
            request, *args, **kwargs)
        self.response_format["data"] = response_data.data
        self.response_format["status"] = 200
        return Response(self.response_format)

    
    # @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    # def enroll(self, request, pk):
    #     model_name = str(self.model.__name__).lower()
    #     try:
    #         obj = self.model.objects.get(pk=pk)
    #         user = request.user
    #         args = {
    #             'user': user,
    #             model_name: obj,
    #             'service_type':self.service_type
    #         }
    #         query = EventService.objects.filter(**args)
    #         if query.exists():
    #             return self.set_response(
    #                 message=f"user has already enrolled in this {model_name}",
    #                 status=208,
    #                 status_code=status.HTTP_208_ALREADY_REPORTED,
    #                 data=EventServiceSerializer(query[0]).data
    #             )
    #         ev_service = EventService.objects.create(**args)
    #         ev_service.save()
    #         return self.set_response(
    #             message=f'{model_name} successfully added',
    #             data=EventServiceSerializer(ev_service).data,
    #         )
    #     except self.model.DoesNotExist:
    #         return self.set_response(
    #             message=f"requested {model_name} doesn't exist",
    #             error=True,
    #             status=404,
    #             status_code=status.HTTP_404_NOT_FOUND
    #         )
            
    
    @action(methods=['POST'], detail=False, permission_classes=[IsAuthenticated])
    def register(self, request):
        user = request.user
        member = CompetitionMember(
            user=user, has_team=False, is_head=False)
        member.save()

        serializer = self.serializer_class(member)
        # put payment module
        return self.set_response(data=serializer.data, message="user added to competition")

    @action(methods=['GET'], detail=False, permission_classes=[IsAuthenticated])
    def is_registered(self, request):
        try:
            email = request.data['email']
            result = CompetitionMember.objects.filter(
                user__email=email, has_team=False).exists()
            if result:
                return self.set_response(data={
                    'available': True
                })
            else:
                return self.set_response(data={
                    'available': False
                }, message="requested user is not registered or already has a team")
        except KeyError as e:
            return self.set_response(error='bad request', status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e1:
            return self.set_response(error=str(e1), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_permissions(self):
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]


class TeamViewSet(ResponseGenericViewSet,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin):
    queryset = Team.objects.all()
    serializer_class = TeamSerialzer
    permission_classes_by_action = {
        'list': [IsAuthenticated],
        'retrive': [IsAuthenticated],
        'destroy': [IsAdminUser],
        'update': [IsAdminUser],
    }

    def retrieve(self, request, *args, **kwargs):
        response_data = super(TeamViewSet, self).retrieve(
            request, *args, **kwargs)
        self.response_format["data"] = response_data.data
        self.response_format["status"] = 200
        if not response_data.data:
            self.response_format["message"] = "Empty"
        return Response(self.response_format)

    def list(self, request, *args, **kwargs):
        response_data = super(TeamViewSet, self).list(
            request, *args, **kwargs)
        self.response_format["data"] = response_data.data
        self.response_format["status"] = 200
        if not response_data.data:
            self.response_format["message"] = "List empty"
        return Response(self.response_format)

    def update(self, request, *args, **kwargs):
        response_data = super(TeamViewSet, self).update(
            request, *args, **kwargs)
        self.response_format["data"] = response_data.data
        self.response_format["status"] = 200

        return Response(self.response_format)

    def destroy(self, request, *args, **kwargs):
        response_data = super(TeamViewSet, self).destroy(
            request, *args, **kwargs)
        self.response_format["data"] = response_data.data
        self.response_format["status"] = 200
        return Response(self.response_format)

    @action(methods=['POST'], detail=False, permission_classes=[IsAuthenticated])
    def create_team(self, request):
        print(request.data)
        try:
            head = CompetitionMember.objects.select_related('user').get(user=request.user)
            if head.has_team:
                raise ValidationError(f"you already have a team !!!")
            head.is_head = True
            head.has_team = True
            team = Team.objects.create(name=request.data['name'])
            members = CompetitionMember.objects.select_related('user').filter(
                user__email__in=request.data['emails'])
            if len(members) > 5 or len(members) < 3:
                raise ValidationError(
                    "count of user members must be between 3 and 5 ")
            for mem in members:
                if mem.has_team:
                    raise ValidationError(
                        f"user {mem.user.user_name} has team")
            head.team = team
            head.save()
            team.save()
            for mem in members:
                team_data = {
                    'head_name': head.user.user_name,
                    'team_name': team.name,
                    'email': mem.user.email,
                    'first_name':mem.user.first_name,
                    'tid':team.pk,
                    'mid':mem.pk
                }
                send_team_requests_task.delay(team_data)
            return Response(data=self.serializer_class(team).data)
        except CompetitionMember.DoesNotExist as e:
            return self.set_response(error=str(e))
        except ValidationError as e1:
            return self.set_response(error=str(e1))
        except Exception as e2:
            return self.set_response(error=str(e2))

    def get_permissions(self):
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]


class PresenterViweSet(ResponseModelViewSet):
    queryset = Presenter.objects.all()
    serializer_class = PresenterSerializer
    # set permission for built_in routes
    permission_classes_by_action = {
        'create': [IsAdminUser],
        'list': [AllowAny],
        'retrive': [AllowAny],
        'destroy': [IsAdminUser],
        'update': [IsAdminUser],
    }


class VerifyTeamRequestView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request, tid, mid):
        tid = force_text(urlsafe_base64_decode(tid))
        mid = force_text(urlsafe_base64_decode(mid))
        try:
            member = CompetitionMember.objects.get(pk=mid)
            team = Team.objects.get(pk=tid)
            if member.has_team:
                data = {
                    'message': 'User already has a team!!!',
                    'error': None,
                    'status': 200,
                    'data': []
                }
                return Response(data=data, status=status.HTTP_200_OK)  
            members_num = team.members.count()
            if members_num > 5:
                data = {
                    'message': 'team is full!!!',
                    'error': None,
                    'status': 200,
                    'data': []
                }
                return Response(data=data, status=status.HTTP_200_OK)  
            member.has_team = True
            member.team = team
            member.save()
            if members_num >=3:
                team.state = 'AC'
            team.save()
            data = {
                'message': 'user activated',
                'error': None,
                'status': 202,
                'data': CompetitionMemberSerializer(member).data
            }
            return Response(data=data, status=status.HTTP_202_ACCEPTED)
        except CompetitionMember.DoesNotExist as e:
            data = {
                'message': 'user not found',
                'error': str(e),
                'status': 400,
                'data': []
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        except Team.DoesNotExist as e1:
            data = {
                'message': 'team not found',
                'error': str(e1),
                'status': 400,
                'data': []
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e2:
            data = {
                'message': 'something went wrong',
                'error': str(e2),
                'status': 400,
                'data': []
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        