from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
 
 
from .models import AssignmentModel, SubmissionModel
from .serializers import (
    
    AssignmentSerializer,
    AssignmentDetailSerializer,
    SubmissionCreateSerializer,
    SubmissionListSerializer,
    SubmissionGradeSerializer,
)
from apps.common.permissions import (
    IsTeacher,
    IsStudent,
    IsOwnerTeacher,
    IsOwnerStudent,
    IsAdminOrTeacher,
)
from .services import mark_late_if_needed, grade_submission



# ══════════════════════════════════════════════
#  ASSIGNMENT VIEWS
# ══════════════════════════════════════════════
 
class AssignmentListAPIView(generics.ListAPIView):
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        
        user = self.request.user
        
        if user.is_student:
            group = user.student_profile.group
            return AssignmentModel.objects.filter(
                group = group,
                is_published = True,
                ).select_related("teacher", "subject")
        if user.is_teacher:
            return AssignmentModel.objects.filter(
                teacher = user.teacher_profile,
                ).select_related("subject","group")
    
        return AssignmentModel.objects.all().select_related("teacher","subject","group")
    

class AssignmentCreateAPIView(generics.CreateAPIView):
    serializer_class = AssignmentSerializer
    permission_classes = [IsTeacher]
    
    def perform_create(self, serializer):
        serializer.save(teacher = self.request.user.teacher_profile)


class AssignmentDetailAPIView(generics.RetrieveAPIView):
    serializer_class = AssignmentDetailSerializer
    permission_classes = [IsAuthenticated]
    queryset = AssignmentModel.objects.select_related("teacher" , "subject" , "group")

class AssignmentUpdateAPIView(generics.UpdateAPIView):
    serializer_class = AssignmentSerializer
    permission_classes = [IsTeacher , IsOwnerTeacher]
    queryset = AssignmentModel.objects.all()
    
    
class AssignmentDeleteAPIView(generics.DestroyAPIView):
    permission_classes = [IsTeacher , IsOwnerTeacher]
    queryset = AssignmentModel.objects.all()
    
class GroupAssignmentListAPIView(generics.ListAPIView):
    serializer_class = AssignmentModel
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        group_id = self.kwargs['group_id']
        return AssignmentModel.objects.filter(
            group_id = group_id,
            is_published = True,
        ).select_related('teacher' , 'subject')
        
        
class SubmissionCreateAPIView(generics.CreateAPIView):
    serializer_class = SubmissionCreateSerializer
    permission_classes = [IsStudent]
    
    def perform_create(self, serializer):
        submission = serializer.save(student = self.request.user.student_profile)
        mark_late_if_needed(submission)
        
        
class SubmissionListAPIView(generics.ListAPIView):
    serializer_class = SubmissionListSerializer
    permission_classes = [IsAdminOrTeacher]
    
    def get_queryset(self):
        
        user = self.request.user
        
        if user.is_teacher:
            return SubmissionModel.objects.filter(
                assignment__teacher = user.teacher_profile,
            ).select_related('student','assignment')
        return SubmissionModel.objects.all().select_related("student" , 'assignment')
    
class SubmissionDetailAPIView(generics.RetrieveAPIView):
    serializer_class = SubmissionListAPIView
    permission_classes = [IsAuthenticated]
    queryset = SubmissionModel.objects.select_related("student" , "assignment")
    
    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        
        if user.is_student and obj.student.user != user:
            raise PermissionDenied("Siz faqat o'z javobingizni ko'ra olasiz.")
        
        if user.is_teacher and obj.assignment.teacher.user != user:
            raise PermissionDenied("Bu sizning assignmentingizga tegishli emas.")
        
        return obj
        
        
class SubmissionGradeAPIView(generics.UpdateAPIView):
    serializer_class = SubmissionGradeSerializer
    permission_classes = {IsTeacher}
    queryset = SubmissionModel.objects.select_related("assignment__teacher")
    http_method_names = ["patch"]
    
    
    def get_object(self):
        obj = super().get_object()
        
        if obj.assignment.teacher.user != self.request.user:
             raise PermissionDenied("Siz faqat o'z talabalaringizni baholaysiz.")
        return obj
 
    def perform_update(self, serializer):
        score    = serializer.validated_data.get("score")
        feedback = serializer.validated_data.get("feedback", "")
        grade_submission(self.get_object(), score, feedback)
 