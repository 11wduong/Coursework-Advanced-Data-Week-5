FROM public.ecr.aws/lambda/python:3.12

# Install ODBC drivers and dependencies
RUN microdnf install -y unixODBC

# Download and install Microsoft ODBC Driver for SQL Server
RUN curl https://packages.microsoft.com/config/rhel/9/prod.repo > /etc/yum.repos.d/mssql-release.repo && \
    ACCEPT_EULA=Y microdnf install -y msodbcsql18

# Copy requirements and install Python dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy application code
COPY extract.py ${LAMBDA_TASK_ROOT}/
COPY transform.py ${LAMBDA_TASK_ROOT}/
COPY load.py ${LAMBDA_TASK_ROOT}/
COPY main.py ${LAMBDA_TASK_ROOT}/

# Set the Lambda handler
CMD ["main.handler"]