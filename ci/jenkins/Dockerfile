# Jenkins controller with the CLIs the pipeline needs baked in:
# docker CLI (talks to the host daemon via the mounted socket), kubectl, helm,
# sonar-scanner, and Python for running tests.
FROM jenkins/jenkins:lts-jdk21

USER root

ARG KUBECTL_VERSION=v1.33.1
ARG HELM_VERSION=v3.18.3
ARG SONAR_SCANNER_VERSION=6.2.1.4610
# Set automatically by BuildKit: amd64 on Intel/Windows, arm64 on Apple Silicon
ARG TARGETARCH=amd64

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl gnupg unzip python3 python3-venv python3-pip \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
    && echo "deb [signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
       > /etc/apt/sources.list.d/docker.list \
    && apt-get update && apt-get install -y --no-install-recommends docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

RUN SCANNER_ARCH=$([ "$TARGETARCH" = "arm64" ] && echo aarch64 || echo x64) \
    && curl -fsSLo /usr/local/bin/kubectl "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${TARGETARCH}/kubectl" \
    && chmod +x /usr/local/bin/kubectl \
    && curl -fsSL "https://get.helm.sh/helm-${HELM_VERSION}-linux-${TARGETARCH}.tar.gz" | tar -xz -C /tmp \
    && mv /tmp/linux-${TARGETARCH}/helm /usr/local/bin/helm \
    && curl -fsSLo /tmp/scanner.zip "https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-${SONAR_SCANNER_VERSION}-linux-${SCANNER_ARCH}.zip" \
    && unzip -q /tmp/scanner.zip -d /opt \
    && ln -s /opt/sonar-scanner-${SONAR_SCANNER_VERSION}-linux-${SCANNER_ARCH}/bin/sonar-scanner /usr/local/bin/sonar-scanner \
    && rm -rf /tmp/*

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
