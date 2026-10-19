// CI/CD pipeline for k8s-rag-chatbot (local lab: Jenkins + SonarQube + kind).
// Each stage is a gate — any failure stops the run before anything is deployed.
pipeline {
  agent any

  options {
    timestamps()
    timeout(time: 30, unit: 'MINUTES')
    buildDiscarder(logRotator(numToKeepStr: '20'))
    disableConcurrentBuilds()
  }

  // GitHub can't reach a laptop, so poll instead of using a webhook.
  triggers { pollSCM('H/2 * * * *') }

  environment {
    REGISTRY      = 'localhost:5001'
    IMAGE_NAME    = 'k8s-rag-chatbot'
    NAMESPACE     = 'chatbot'
    RELEASE       = 'chatbot'
    CHART         = 'k8s/helm/k8s-rag-chatbot'
    TRIVY_VERSION = '0.58.1'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        script {
          // Immutable tag: every image traces back to exactly one commit.
          env.IMAGE_TAG = sh(script: 'git rev-parse --short=8 HEAD', returnStdout: true).trim()
          env.IMAGE     = "${env.REGISTRY}/${env.IMAGE_NAME}:${env.IMAGE_TAG}"
        }
        echo "Building ${env.IMAGE}"
      }
    }

    stage('Unit tests') {
      steps {
        sh '''
          python3 -m venv .venv
          . .venv/bin/activate
          pip install -q -r requirements-dev.txt
          pytest --junitxml=test-results.xml \
                 --cov=backend --cov-report=xml:coverage.xml --cov-report=term
        '''
      }
      post {
        always { junit 'test-results.xml' }
      }
    }

    stage('SonarQube analysis') {
      steps {
        withSonarQubeEnv('sonarqube') {
          sh 'sonar-scanner -Dsonar.projectVersion=${IMAGE_TAG}'
        }
      }
    }

    stage('Quality gate') {
      steps {
        // SonarQube calls back to Jenkins via webhook when analysis finishes.
        timeout(time: 5, unit: 'MINUTES') {
          waitForQualityGate abortPipeline: true
        }
      }
    }

    stage('Docker build') {
      steps {
        sh 'docker build --pull -t ${IMAGE} .'
      }
    }

    stage('Trivy image scan') {
      steps {
        sh '''
          docker run --rm \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -v trivy-cache:/root/.cache \
            aquasec/trivy:${TRIVY_VERSION} image \
              --severity CRITICAL --ignore-unfixed --exit-code 1 \
              --no-progress ${IMAGE}
        '''
      }
    }

    stage('Push image') {
      steps {
        sh 'docker push ${IMAGE}'
      }
    }

    stage('Deploy with Helm') {
      when { expression { env.BRANCH_NAME == null || env.BRANCH_NAME == 'main' } }
      steps {
        withCredentials([file(credentialsId: 'kind-kubeconfig', variable: 'KUBECONFIG')]) {
          // --atomic rolls back automatically if new pods never become ready.
          sh '''
            helm upgrade --install ${RELEASE} ${CHART} \
              --namespace ${NAMESPACE} \
              --set image.repository=${REGISTRY}/${IMAGE_NAME} \
              --set image.tag=${IMAGE_TAG} \
              --atomic --wait --timeout 5m
          '''
        }
      }
    }

    stage('Smoke test') {
      when { expression { env.BRANCH_NAME == null || env.BRANCH_NAME == 'main' } }
      steps {
        withCredentials([file(credentialsId: 'kind-kubeconfig', variable: 'KUBECONFIG')]) {
          sh '''
            kubectl -n ${NAMESPACE} run smoke-${BUILD_NUMBER} --rm -i --restart=Never \
              --image=curlimages/curl -- \
              curl -sf http://${RELEASE}-k8s-rag-chatbot/api/v1/health
          '''
        }
      }
    }
  }

  post {
    success { echo "Deployed ${env.IMAGE} to namespace ${env.NAMESPACE}" }
    failure { echo 'Pipeline failed — nothing was deployed past the failing stage.' }
    always {
      sh 'docker image rm ${IMAGE} || true'
      cleanWs()
    }
  }
}
