FROM apify/actor-python:3.12

COPY requirements.txt ./
RUN echo "Python version:" \
 && python --version \
 && echo "Installing dependencies:" \
 && pip install --no-cache-dir -r requirements.txt \
 && echo "All installed Python packages:" \
 && pip freeze

# `src/govkit` is vendored in by scripts/build_actor.py at deploy time so that
# every actor ships the same audited core without a private package registry.
COPY . ./

RUN python -m compileall -q src

CMD ["python", "-m", "src"]
