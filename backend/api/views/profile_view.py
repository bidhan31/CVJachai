from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, serializers
from api.models import Profile
from django.contrib.auth.models import User

# --- Serializers ---

class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = Profile
        fields = (
            'email', 'first_name', 'last_name', 'location', 
            'profession', 'skills', 'company_name', 'bio', 
            'phone_number', 'website'
        )

# --- Views ---

class ProfileDetailAPIView(APIView):
    """
    Manage the currently authenticated user's profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """View the current profile."""
        # Ensure profile exists (for older users created before migrations)
        profile, created = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """Update the current profile."""
        profile, created = Profile.objects.get_or_create(user=request.user)
        user = request.user

        # Handle updating first_name/last_name on the User model
        user_data = {}
        if 'first_name' in request.data:
            user.first_name = request.data['first_name']
        if 'last_name' in request.data:
            user.last_name = request.data['last_name']
        user.save()

        # Update the Profile model
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Profile updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
