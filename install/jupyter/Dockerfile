# Dyalog APL + JupyterLab + Dyalog's Jupyter kernel.
# Build: install/jupyter/build.sh     Run: install/jupyter/jupyter.sh start
FROM docker.io/dyalog/dyalog:latest

ARG JUPYTERLAB_VERSION=4.6.4
ARG KERNEL_VERSION=2.0.2

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-venv \
 && rm -rf /var/lib/apt/lists/* \
 && python3 -m venv /opt/jupyter \
 && /opt/jupyter/bin/pip install --no-cache-dir \
      "jupyterlab==${JUPYTERLAB_VERSION}" "dyalog-jupyter-kernel==${KERNEL_VERSION}" nbconvert \
 # Register the kernel inside the venv (the kernel's own installer registers it
 # per user, which in a container depends on who runs it)
 && KS="$(/opt/jupyter/bin/python -c 'import dyalog_kernel, os; print(os.path.join(os.path.dirname(dyalog_kernel.__file__), "dyalog_apl"))')" \
 && /opt/jupyter/bin/jupyter kernelspec install "$KS" --sys-prefix \
 && /opt/jupyter/bin/jupyter kernelspec list \
 # The kernel (2.0.2) looks for /opt/mdyalog/<ver>/64/unicode/mapl, the launcher
 # name used by the Mac app and older Linux installs. This image's launcher
 # is the dyalog binary itself, so give it that name too.
 && ln -s dyalog "$(dirname "$(readlink -f /usr/bin/dyalog)")/mapl"
ENV PATH=/opt/jupyter/bin:$PATH
USER dyalog
WORKDIR /app
EXPOSE 8888
# The kernel starts its own Dyalog (found as `dyalog` on PATH) and talks to it
# over the RIDE protocol; we only need to start Jupyter.
ENTRYPOINT ["jupyter"]
CMD ["lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--notebook-dir=/app/notebooks"]
