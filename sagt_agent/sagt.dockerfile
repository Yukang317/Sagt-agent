FROM langchain/langgraph-api:3.12-wolfi-d18f703



# -- Adding local package . --
ADD . /deps/sagt_agent
# -- End of local package . --

# -- Adding non-package dependency src --
ADD ./src /deps/outer-src/src
RUN set -ex && \
    for line in '[project]' \
                'name = "src"' \
                'version = "0.1"' \
                '[tool.setuptools.package-data]' \
                '"*" = ["**/*"]' \
                '[build-system]' \
                'requires = ["setuptools>=61"]' \
                'build-backend = "setuptools.build_meta"'; do \
        echo "$line" >> /deps/outer-src/pyproject.toml; \
    done
# -- End of non-package dependency src --

# -- Installing all local dependencies --
RUN for dep in /deps/*; do             echo "Installing $dep";             if [ -d "$dep" ]; then                 echo "Installing $dep";                 (cd "$dep" && PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir -c /api/constraints.txt -e .);             fi;         done
# -- End of local dependencies install --
# 免费版smith账号不需要auth认证
#ENV LANGGRAPH_AUTH='{"path": "/deps/outer-src/src/auth/auth.py:auth"}'
ENV LANGGRAPH_HTTP='{"app": "/deps/sagt_agent/src/webapp/webapp.py:app"}'
ENV LANGSERVE_GRAPHS='{"sagt": "/deps/sagt_agent/src/graphs/sagt_graph/sagt_graph.py:graph"}'



# -- Ensure user deps didn't inadvertently overwrite langgraph-api
RUN mkdir -p /api/langgraph_api /api/langgraph_runtime /api/langgraph_license && touch /api/langgraph_api/__init__.py /api/langgraph_runtime/__init__.py /api/langgraph_license/__init__.py
RUN PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir --no-deps -e /api
# -- End of ensuring user deps didn't inadvertently overwrite langgraph-api --
# -- Removing build deps from the final image ~<:===~~~ --
RUN pip uninstall -y pip setuptools wheel
RUN rm -rf /usr/local/lib/python*/site-packages/pip* /usr/local/lib/python*/site-packages/setuptools* /usr/local/lib/python*/site-packages/wheel* && find /usr/local/bin -name "pip*" -delete || true
RUN rm -rf /usr/lib/python*/site-packages/pip* /usr/lib/python*/site-packages/setuptools* /usr/lib/python*/site-packages/wheel* && find /usr/bin -name "pip*" -delete || true
RUN uv pip uninstall --system pip setuptools wheel && rm /usr/bin/uv /usr/bin/uvx

WORKDIR /deps/sagt_agent