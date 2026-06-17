from rest_framework import serializers
from .models import AssignmentModel , SubmissionModel
from django.utils import timezone


class AssignmentSerializer(serializers.ModelSerializer):
    teacher_name = serializers.ReadOnlyField(source = "teacher.user.full_name")
    attachment_url = serializers.SerializerMethodField()
    
    class Meta:
        model = AssignmentModel
        fields = fields = [
            "id",
            "title",
            "description",
            "teacher",        
            "teacher_name",   
            "subject",
            "group",
            "due_date",
            "max_score",
            "attachment",
            "attachment_url",
            "is_published",
            "created_at",
        ]
        read_only_fields = ["teacher", "created_at"]
        
        def get_attachment_url(self, obj):
            request = self.context.get('request')
            if obj.attachment and request:
                return request.build_absolute_uri(obj.attachment.url)
            return None
        
        def vaidate_max_score(self, value):
            if value <= 0:
                 raise serializers.ValidationError("Maksimal ball 0 dan katta bo'lishi kerak.")
            return value
        
        def validate_due_date(self ,value):
            if timezone < value:
                 raise serializers.ValidationError("Deadline o'tib ketgan sana bo'lishi mumkin emas.")
            return value
                 
 
class AssignmentDetailSerializer(AssignmentSerializer):
    submissions_count = serializers.SerializerMethodField()
    
    class Meta(AssignmentSerializer.Meta):
        fields = AssignmentSerializer.Meta.fields + ['submissions_count']
         
    def get_submissions_count(self , obj):
        return obj.submissions.count()
        
        
        
# ──────────────────────────────────────────────
#  SUBMISSION SERIALIZERS
# ──────────────────────────────────────────────
 
class SubmissionCreateSerializer(serializers.ModelSerializer):        
  
    class Meta:
        model = SubmissionModel
        fields = [
            "id",
            "assignment",
            "content",
            "attachment",
            ]
    def validate(self, attrs):
        student = self.context['request'].user.student_profile 
        assignment = attrs.get("assignment")

        already_submitted = SubmissionModel.objects.filter(
            assignment=assignment,
            student = student
        ).exists()
       
        if already_submitted:
             raise serializers.ValidationError("Siz bu vazifani allaqachon topshirgansiz.")
 
        return attrs
    
    def validate_assignment(self , value):
        if timezone.now() > value.due_date:
            raise serializers.ValidationError("Deadline tugagan. Endi topshirib bo'lmaydi.")
        return value  
    
class SubmissionListSerializer(serializers.ModelSerializer):
    
    student_name = serializers.ReadOnlyField(source = 'student.user.full_name')
    assignment_title  = serializers.ReadOnlyField(source = 'assignment.title')
    attachment_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SubmissionModel
        fields = [
            "id",
            "assignment",
            "assignment_title",
            "student",
            "student_name",
            "content",
            "attachment",
            "attachment_url",
            "submitted_at",
            "status",
            "score",
            "is_late",
        ]
        
    def get_attachment_url(self, obj):
        request = self.context.get("request")
        if obj.attachment and request:
            return request.build_absolute_uri(obj.attachment.url)
        return None
    
    
    
class SubmissionGradeSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubmissionModel
        fields = ["score", "status", "feedback", "graded_at"]    
        
    def validate_score(self, value):
        """Ball 0 dan katta va max_score dan oshmasligi kerak."""
        if value is None:
            return value
        submission = self.instance  
        if value < 0:
            raise serializers.ValidationError("Ball manfiy bo'lishi mumkin emas.")
        if value > submission.assignment.max_score:
            raise serializers.ValidationError(
                f"Ball {submission.assignment.max_score} dan oshmasligi kerak."
            )
        return value
 
    def validate_status(self, value):
        """Faqat ruxsat etilgan statuslarni qabul qiladi."""
        allowed = [
            SubmissionModel.StatusChoices.GRADED,
            SubmissionModel.StatusChoices.RETURNED,
        ]
        if value not in allowed:
            raise serializers.ValidationError("Faqat 'graded' yoki 'returned' qo'ysa bo'ladi.")
        return value