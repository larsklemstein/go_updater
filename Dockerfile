FROM python:3.12.2-slim as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1


FROM base AS python-deps

# Install pipenv and compilation dependencies
RUN pip install pipenv
RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Install python dependencies in /.venv
COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy


FROM base AS runtime

# Copy virtual env from python-deps stage
COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

# Adjust user and group ID to your own local ids!!!

RUN groupadd -g 1000 appuser
RUN useradd -u 1000 -g appuser --create-home appuser
WORKDIR /home/appuser
USER appuser

RUN mkdir /home/appuser/app

# Install application into container
COPY go_updater.py .

ENTRYPOINT ["python", "go_updater.py"]
