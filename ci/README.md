# Local CI/CD lab

Every push to `main` runs through Jenkins and lands in a local Kubernetes cluster — no cloud account needed.

```
push → Jenkins → pytest → SonarQube quality gate → docker build → Trivy scan
     → push to local registry → helm upgrade --atomic → smoke test
```

Any failing stage stops the run, so broken or vulnerable code never reaches the cluster.

| Piece | Runs as | URL |
|---|---|---|
| Jenkins | container | http://localhost:8080 |
| SonarQube + Postgres | containers | http://localhost:9000 |
| Image registry | container | localhost:5001 |
| Kubernetes | kind cluster `ci` (single node) | `kubectl` |

## Prerequisites

Docker Desktop (Memory 4 GB, Swap 2 GB — sized for an 8 GB laptop), [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation), kubectl, and a `.env` in the repo root with `OPENAI_API_KEY`, `PINECONE_API_KEY`, `PINECONE_INDEX`.

On Linux only, SonarQube's Elasticsearch needs: `sudo sysctl -w vm.max_map_count=524288`

## 1. Start the lab

```bash
./ci/setup.sh
```

Creates the cluster, starts Jenkins/SonarQube/registry, wires the registry into the cluster, creates the `chatbot` namespace and API-key Secret, and writes `ci/kubeconfig-jenkins.yaml` (gitignored).

## 2. Configure SonarQube (once)

1. Log in at http://localhost:9000 with `admin` / `admin` and set a new password.
2. **My Account → Security →** generate a **Global Analysis Token**. Copy it.
3. **Administration → Configuration → Webhooks → Create:** name `jenkins`, URL `http://jenkins:8080/sonarqube-webhook/`
   (This is how Jenkins learns the quality-gate result.)

## 3. Configure Jenkins (once)

1. Open http://localhost:8080. Unlock with `docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword`, choose **Select plugins → None** (plugins are preinstalled), create your admin user.
2. **Manage Jenkins → Credentials → (global) → Add:**
   - *Secret text*, ID `sonar-token`, value = the SonarQube token
   - *Secret file*, ID `kind-kubeconfig`, file = `ci/kubeconfig-jenkins.yaml`
3. **Manage Jenkins → System → SonarQube servers:** tick *Environment variables*, add server name `sonarqube`, URL `http://sonarqube:9000`, token `sonar-token`.
4. **New Item → Pipeline** named `k8s-rag-chatbot`. Under *Pipeline*: *Pipeline script from SCM* → Git → `https://github.com/GaneshSaiD/k8s-rag-chatbot.git`, branch `*/main`, script path `Jenkinsfile`.
5. **Build Now.** After the first run, Jenkins polls GitHub every ~2 minutes.

## 4. See it running

```bash
kubectl -n chatbot get pods
kubectl -n chatbot port-forward svc/chatbot-k8s-rag-chatbot 8000:80
curl localhost:8000/api/v1/health
```

## Things to try (this is where the learning happens)

- **Break a test** → the run stops at *Unit tests*; nothing is built.
- **Add a code smell** or drop coverage → SonarQube fails the gate; pipeline aborts.
- **Change the base image to an old one** (e.g. `python:3.8-slim`) → Trivy blocks the push.
- **Point the readiness probe at a bad path** → `helm --atomic` rolls back to the previous release on its own.
- `helm -n chatbot history chatbot` → every release maps to a git SHA; `helm rollback chatbot <rev>` to go back.

## Tear down

```bash
docker compose -f ci/docker-compose.yml down     # add -v to wipe Jenkins/Sonar data
kind delete cluster --name ci
```

## How this maps to production on AWS

| Local lab | Production equivalent |
|---|---|
| kind cluster | EKS (provisioned with Terraform) |
| `localhost:5001` registry | Amazon ECR |
| Secret from `.env` | AWS Secrets Manager + External Secrets Operator |
| `pollSCM` | GitHub webhook |
| Jenkins with host Docker socket | Jenkins agents on EKS (Kaniko/BuildKit, no socket) |
| `helm upgrade` from Jenkins | Same, or Argo CD (GitOps) |

The Jenkinsfile stages stay the same; only the registry URL, credentials, and cluster change.
