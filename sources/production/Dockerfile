FROM public.ecr.aws/lambda/python:3.9

RUN pip install -U pip
RUN pip install pipenv

# Absolute paths on Windows
COPY ["Pipfile", "Pipfile.lock", "./"]

# You can enforce that your Pipfile.lock is up to date using the --deploy flag:
# This will fail a build if the Pipfile.lock is out–of–date, instead of generating a new one.
# You can tell Pipenv to install a Pipfile’s contents into its parent system with the --system flag:
RUN pipenv install --system --deploy

COPY ["chicago_taxi_prediction.py", "model_service.py", "./"]

CMD ["chicago_taxi_prediction.lambda_handler"]
