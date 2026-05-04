from django.urls import path
from .views import *

urlpatterns = [
    path('jobs/', JobListView.as_view()),
    path('jobs/create/', JobCreateView.as_view()),
    path('jobs/<uuid:pk>/trigger/', JobTriggerView.as_view()),
    path('jobs/<uuid:pk>/stages/', JobStagesView.as_view()),
    path('jobs/<uuid:pk>/summary/', JobSummaryView.as_view()),
    path('stages/<uuid:stage_id>/logs/', StageLogCreateView.as_view()),
]