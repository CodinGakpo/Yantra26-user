from django.urls import path
from .views import (
    IssueReportListCreateView, presign_s3, presign_get_for_track,
    CommunityResolvedIssuesView, UserIssueHistoryView,
    CommentListCreateView, ToggleLikeView, ToggleDislikeView
)

urlpatterns = [
    path("", IssueReportListCreateView.as_view(), name="report-management"),
    path("s3/presign/", presign_s3, name="presign-s3"),
    path("<int:id>/presign-get/", presign_get_for_track, name="presign-get"),
    path("community/resolved/", CommunityResolvedIssuesView.as_view()),
    path("history/", UserIssueHistoryView.as_view(), name="user-issue-history"),
    
    # Social Endpoints
    path("<int:report_id>/comments/", CommentListCreateView.as_view(), name="report-comments"),
    path("<int:report_id>/like/", ToggleLikeView.as_view(), name="report-like"),
    path("<int:report_id>/dislike/", ToggleDislikeView.as_view(), name="report-dislike"),
]