FROM public.ecr.aws/lambda/python:3.12


# Copy requirements and install Python dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy application code
COPY extract.py ${LAMBDA_TASK_ROOT}/
COPY transform.py ${LAMBDA_TASK_ROOT}/
COPY load.py ${LAMBDA_TASK_ROOT}/
COPY pipeline.py ${LAMBDA_TASK_ROOT}/

# Set the Lambda handler
CMD ["pipeline.handler"]
