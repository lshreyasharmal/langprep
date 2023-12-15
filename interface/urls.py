from . import views
from rest_framework.routers import SimpleRouter
from .views import DropBoxViewset
from .views import S3FileDownloadView, S3FileReadView
from django.urls import path
from .views import CustomTemplateView

router = SimpleRouter()
router.register('uploader', DropBoxViewset)
urlpatterns = router.urls


urlpatterns += [
    path('textextract/<str:file_key>/', S3FileDownloadView.as_view(), name='extractText'),
    path('custom-template/', CustomTemplateView.as_view(), name='custom_template'),
    path('read/<str:file_key>/', S3FileReadView.as_view(), name='ReadText'),
    # Add other urlpatterns as needed
]
