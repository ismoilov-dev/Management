from rest_framework.permissions import BasePermission


class IsTeacher(BasePermission):
    """
    Faqat 'teacher' rolidagi foydalanuvchi o'ta oladi.
    CustomUser modelidagi role fieldini tekshiradi.
    """

    message = "Bu amal faqat o'qituvchilar uchun."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_teacher 
        )


class IsStudent(BasePermission):
    """Faqat 'student' rolidagi foydalanuvchi o'ta oladi."""

    message = "Bu amal faqat talabalar uchun."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_student  
        )


class IsOwnerTeacher(BasePermission):
    """
    Object-level permission:
    Teacher faqat O'ZI yaratgan assignmentni o'zgartira oladi.
    """
    message = "Siz faqat o'z vazifalaringizni boshqara olasiz."
    def has_object_permission(self, request, view, obj):
        return obj.teacher.user == request.user


class IsOwnerStudent(BasePermission):
    """
    Student faqat O'ZI yuborgan submissionni ko'ra oladi.
    """
    message = "Siz faqat o'z javobingizni ko'ra olasiz."
    def has_object_permission(self, request, view, obj):
        return obj.student.user == request.user


class IsAdminOrTeacher(BasePermission):
    """Admin yoki teacher o'ta oladi (submission ro'yxatini ko'rish uchun)."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (request.user.is_admin or request.user.is_teacher)
        )