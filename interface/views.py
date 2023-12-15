from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.shortcuts import redirect
import boto3
from django.conf import settings
from rest_framework import viewsets, parsers
from .models import DropBox
from .serializers import DropBoxSerializer
from django.http import FileResponse
from django.views import View
from django.core.files.storage import default_storage
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponseRedirect
import os 


class DropBoxViewset(viewsets.ModelViewSet):
 
    queryset = DropBox.objects.all()
    serializer_class = DropBoxSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def create(self, request, *args, **kwargs):
        for filename, file in request.FILES.items():
            title = request.FILES[filename].name
        request.data['title']=title
        response = super().create(request, *args, **kwargs)
        # Assuming 'success_url' is the URL you want to redirect to
        return HttpResponseRedirect('http://127.0.0.1:8081/custom-template/')

class CustomTemplateView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'interface/custom_template.html'

    def get(self, request, *args, **kwargs):
        queryset = DropBox.objects.all()
        serializer = DropBoxSerializer(queryset, many=True)
        return Response({'data': serializer.data})


class S3FileDownloadView(View):
    def get(self, request, file_key, *args, **kwargs):
        # Construct the full S3 URL for the file
        file_url = default_storage.url(file_key)

        # Get the file name from the URL
        file_name = file_url.split('/')[-1]

        # Open the file and create a FileResponse
        file = default_storage.open(file_key)
        response = FileResponse(file)

        response_text = extract_text_from_file(file)
        # Set the content disposition header for the browser to prompt a download
        # response['Content-Disposition'] = f'attachment; filename="{file_name}"'

        return HttpResponse(response_text)
    
class S3FileReadView(View):
    def get(self, request, file_key, *args, **kwargs):
        # Construct the full S3 URL for the file
        file_url = default_storage.url(file_key)

        # Get the file name from the URL
        file_name = file_url.split('/')[-1]

        # Open the file and create a FileResponse
        file = default_storage.open(file_key)
        response = FileResponse(file)

        response_text = extract_text_from_file(file)
        # Set the content disposition header for the browser to prompt a download
        # response['Content-Disposition'] = f'attachment; filename="{file_name}"'

        return synthesize_text(response_text)
    

def extract_text_from_file(file):
    # Initialize a Textract client
    file_text = ""
    textract_client = boto3.client('textract', region_name=settings.AWS_S3_REGION_NAME)

    response = textract_client.start_document_text_detection(
            DocumentLocation={
        'S3Object': {
            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'Name': file.name
        }
    })
        

    # Get the JobId from the response
    job_id = response['JobId']

    # Wait for the Textract job to complete
    response = textract_client.get_document_text_detection(JobId=job_id)
    while response['JobStatus'] == 'IN_PROGRESS':
        response = textract_client.get_document_text_detection(JobId=job_id)

    # Check if the job was successful
    if response['JobStatus'] == 'SUCCEEDED':
        # Extract and print the detected text
        for item in response['Blocks']:
            if item['BlockType'] == 'LINE':
                file_text += item['Text'] + " "
        print(file_text)
        return file_text
    else:
        print(f"Textract job failed: {response['StatusMessage']}")
        return f"Textract job failed: {response['StatusMessage']}"
    


def synthesize_text(text, voice_id='Joanna', output_format='mp3'):
    # Create an Amazon Polly client
    polly = boto3.client('polly')

    # Specify the text, voice, and output format
    response = polly.synthesize_speech(
        Text=text,
        VoiceId=voice_id,
        OutputFormat=output_format
    )

    # Save the audio stream to a file
    with open('output.mp3', 'wb') as file:
        file.write(response['AudioStream'].read())
    file = open("output.mp3", "rb").read()
    os.remove("output.mp3")
    response['Content-Disposition'] = 'attachment; filename=filename.mp3' 
    return HttpResponse(file, content_type="audio/mpeg") 



