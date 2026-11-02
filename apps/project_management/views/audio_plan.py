# class AudioBatchDataUploadView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def post(self, request, *args, **kwargs):
#         serializer = AudioBatchDataSerializer(data=request.data, context={'request': request})
#
#         if serializer.is_valid():
#             serializer.save()
#             batch = ImagePlan.objects.get(id=request.data['batch'])
#             batch.update_status('processing')
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)