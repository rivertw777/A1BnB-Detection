# Use a slim version of the base Python image to reduce the final image size
FROM python:3.10-slim

RUN apt update
RUN apt install -y libgl1-mesa-glx
RUN apt install -y libglib2.0-0

# Define custom function directory
ARG FUNCTION_DIR="/detection"

RUN mkdir -p ${FUNCTION_DIR}
COPY . ${FUNCTION_DIR}

# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}

# Install the runtime interface client
RUN pip install awslambdaric

# Install requirements.txt
RUN pip install -r requirements.txt

# Set runtime interface client as default command for the container runtime
ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]

# entrypoint 실행시 argument로써 전달
CMD [ "lambda_function.lambda_handler" ]