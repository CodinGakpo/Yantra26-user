from django.utils.crypto import get_random_string
from rest_framework import serializers
from .models import IssueReport, Comment

class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.first_name', read_only=True) # Or user.username depending on your User model
    
    class Meta:
        model = Comment
        fields = ['id', 'user', 'username', 'text', 'created_at']
        read_only_fields = ['id', 'user', 'username', 'created_at']
class IssueReportSerializer(serializers.ModelSerializer):
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    dislikes_count = serializers.IntegerField(source='dislikes.count', read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_disliked = serializers.SerializerMethodField()

    class Meta:
        model = IssueReport
        fields = "__all__"
        read_only_fields = ("id", "issue_date", "updated_at", "status", "user", "tracking_id", "likes", "dislikes")

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

    def get_is_disliked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.dislikes.filter(id=request.user.id).exists()
        return False

    def _generate_unique_tracking_id(self) -> str:
        allowed_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        while True:
            tid = get_random_string(8, allowed_chars)
            if not IssueReport.objects.filter(tracking_id=tid).exists():
                return tid

    def create(self, validated_data):
        request = self.context.get("request")
        if request and getattr(request, "user", None) and request.user.is_authenticated:
            validated_data.setdefault("user", request.user)

        if not validated_data.get("tracking_id"):
            validated_data["tracking_id"] = self._generate_unique_tracking_id()

        return super().create(validated_data)
    
    def validate_image_url(self, value):
        if value.startswith("http"):
            raise serializers.ValidationError(
                "image_url must be an S3 object key, not a full URL"
            )
        return value
    
class IssueHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueReport
        fields = (
            "tracking_id",
            "issue_title",
            "location",
            "status",
        )