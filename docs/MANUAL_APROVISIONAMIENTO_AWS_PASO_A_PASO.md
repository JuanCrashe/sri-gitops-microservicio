# 🚀 Manual Detallado Paso a Paso: Aprovisionamiento y Despliegue en AWS (Amazon EKS)
## Trabajo de Fin de Máster (TFM) — UNIR
**Proyecto:** Microservicio SRI Facturación — GitOps Multicloud  
**Autores:** Darwin Augusto Calle Loja, Juan Carlos Cela Palacios, Luis Patricio Cuascota Tanicuchi  

---

## 📌 Introducción y Propósito del Documento
Este documento guía paso a paso el aprovisionamiento de la arquitectura en **Amazon Web Services (AWS)** utilizando **Amazon Elastic Kubernetes Service (EKS)**, Infraestructura como Código (IaC) con **Terraform**, y despliegue continuo con **ArgoCD (GitOps)**.

Está diseñado específicamente para:
1. Configurar y autenticar la cuenta de AWS.
2. Aprovisionar el clúster y la infraestructura necesaria para la grabación del video de defensa de 5 minutos.
3. Garantizar un protocolo estricto de **FinOps Teardown** al finalizar para retornar la facturación a **$0.00/h**.

---

## 🗺️ Mapa de Fases del Aprovisionamiento

```
[FASE 1: PREPARACIÓN LOCAL & CREDENCIALES] ✅ COMPLETADA
                        │
                        ▼
[FASE 2: RECURSOS BASE S3 / ECR]           ✅ COMPLETADA
                        │
                        ▼
[FASE 3: TERRAFORM APPLY (CLÚSTER EKS)]    ✅ COMPLETADA (9/9 RECURSOS - 3 NODOS READY)
                        │
                        ▼
[FASE 4: KUBECTL & CONTROLLERS (ALB/CSI)]  ✅ COMPLETADA (METRICS, ARGOCD, CSI, ALB)
                        │
                        ▼
[FASE 5: PARÁMETROS SSM & IMÁGENES ECR]    🟡 EN PROCESO (SECRETOS SSM LISTOS)
                        │
                        ▼
[FASE 6: GITOPS ARGOCD & APLICACIÓN EN VIVO] ⏳ SIGUIENTE PASO
                        │
                        ▼
[FASE 7: DEMO 5 MINUTOS & GRABACIÓN]       ⏳ PENDIENTE
                        │
                        ▼
[FASE 8: FINOPS TEARDOWN LIMPIO ($0.00/h)] ⏳ PENDIENTE
```

---

## 🛠️ Fase 1: Preparación del Entorno Local y Autenticación con AWS (Completada)

### 1.1 Herramientas Verificadas
* **AWS CLI:** `v2.32.16`
* **Terraform:** `v1.16.5`
* **kubectl:** `v1.36.1`
* **Helm:** `v4.3.0`
* **Kustomize:** `v5.8.1`

### 1.2 Configuración de Credenciales
```powershell
aws configure
```
Parámetros configurados:
* **Default region name:** `us-east-1`
* **Default output format:** `json`

### 1.3 Verificación de Identidad STS
```powershell
aws sts get-caller-identity
```
* **Salida de verificación exitosa:**
```json
{
    "UserId": "AIDAZKCMKNRT7G45GEUMV",
    "Account": "640110193767",
    "Arn": "arn:aws:iam::640110193767:user/crashe-cli"
}
```

---

## 🪣 Fase 2: Plataforma Base de Larga Vida (Bucket S3 para Estado y ECR) (Completada)

La infraestructura de larga vida almacena el estado de Terraform y las imágenes de contenedor. Sobrevive al ciclo de vida del clúster EKS para permitir aprovisionar y destruir el clúster bajo demanda sin perder el registro ni el historial.

### 2.1 Creación del Bucket S3 para el Estado Remoto de Terraform
Dado que los nombres de los buckets S3 son únicos a nivel mundial, se utiliza el sufijo del Account ID de la cuenta (`640110193767`):

```powershell
# 1. Crear el bucket en la región us-east-1
aws s3api create-bucket --bucket sri-gitops-tfstate-640110193767 --region us-east-1

# 2. Habilitar versionado (permite recuperar estados previos de Terraform ante incidentes)
aws s3api put-bucket-versioning --bucket sri-gitops-tfstate-640110193767 --versioning-configuration Status=Enabled

# 3. Habilitar cifrado en reposo AES256 por defecto (seguridad exigida por DevSecOps)
aws s3api put-bucket-encryption --bucket sri-gitops-tfstate-640110193767 --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

# 4. Bloquear todo acceso público al bucket (protege el state file que puede contener metadatos sensibles)
aws s3api put-public-access-block --bucket sri-gitops-tfstate-640110193767 --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

### 2.2 Creación de los Repositorios ECR (Elastic Container Registry)
Se crean los dos registros privados donde se almacenarán las imágenes de los microservicios:

```powershell
# Repositorio para la API REST FastAPI
aws ecr create-repository --repository-name sri-backend --region us-east-1 --image-scanning-configuration scanOnPush=true

# Repositorio para el Frontend Flask
aws ecr create-repository --repository-name sri-frontend --region us-east-1 --image-scanning-configuration scanOnPush=true
```
* **Qué hace `scanOnPush=true`:** Habilita el análisis estático automático de vulnerabilidades CVE sin costo adicional cada vez que se sube una imagen Docker.

---

## 🏗️ Fase 3: Aprovisionamiento del Clúster EKS con Terraform (IaC) (Completada)

### 3.1 Inicialización de Terraform con Backend Remoto
```powershell
cd iac/aws
terraform init
```

### 3.2 Despliegue de la Infraestructura en AWS
```powershell
terraform apply -auto-approve
```
* **Resultado del Apply:** `Apply complete! Resources: 9 added, 0 changed, 0 destroyed.`
  1. `module.eks.aws_iam_role.eks_cluster`: Rol IAM para el plano de control de EKS.
  2. `module.eks.aws_iam_role_policy_attachment.eks_cluster_policy`: Permisos administrados de EKS.
  3. `module.eks.aws_eks_cluster.main`: Clúster gestionado EKS (`sri-eks-cluster`).
  4. `module.eks.aws_vpc_security_group_ingress_rule.eks_api`: Reglas de seguridad para el API Server de Kubernetes (puerto 443).
  5. `aws_iam_role.eks_nodes`: Rol IAM para las instancias EC2 (workers).
  6. `aws_iam_role_policy_attachment.eks_nodes` (WorkerNodePolicy).
  7. `aws_iam_role_policy_attachment.eks_nodes` (CNI_Policy para red de pods).
  8. `aws_iam_role_policy_attachment.eks_nodes` (ContainerRegistryReadOnly).
  9. `aws_eks_node_group.main`: Grupo de nodos administrados con 3 instancias `t3.medium`.

---

## ⚙️ Fase 4: Conexión y Controladores Esenciales del Clúster (Completada)

### 4.1 Configuración de Kubeconfig
```powershell
aws eks update-kubeconfig --region us-east-1 --name sri-eks-cluster
kubectl get nodes -o wide
```
* **Resultado:** 3 nodos workers en estado `Ready` corriendo Kubernetes v1.35 en AWS EC2.

### 4.2 Despliegue de Metrics Server (para HPA y Telemetría)
```powershell
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl top nodes
```
* **Resultado:** Pod `metrics-server` en estado `Running` reportando métricas de CPU y memoria en tiempo real.

### 4.3 Despliegue de ArgoCD (Motor GitOps)
```powershell
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v2.11.0/manifests/install.yaml
kubectl get pods -n argocd
```
* **Resultado:** Todos los pods de ArgoCD (`argocd-server`, `argocd-repo-server`, `argocd-application-controller`, etc.) en estado `Running`.

### 4.4 Aprovisionamiento de Secrets Store CSI Driver + AWS Provider
```powershell
# 1. Aprovisionar Rol IAM y Parámetros en iac/aws/secrets-csi
cd iac/aws/secrets-csi
terraform init
terraform apply -auto-approve

# 2. Desplegar el driver y proveedor AWS con Helm
helm repo add --force-update secrets-store-csi-driver https://kubernetes-sigs.github.io/secrets-store-csi-driver/charts
helm repo update secrets-store-csi-driver
helm upgrade --install secrets-store-csi-driver secrets-store-csi-driver/secrets-store-csi-driver `
  --namespace kube-system `
  --version 1.4.8 `
  --set syncSecret.enabled=true `
  --set tokenRequests[0].audience="sts.amazonaws.com" `
  --set tokenRequests[0].expirationSeconds=86400 `
  --set tokenRequests[1].audience="pods.eks.amazonaws.com" `
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"="arn:aws:iam::640110193767:role/sri-eks-cluster-secrets-csi"

kubectl annotate sa secrets-store-csi-driver -n kube-system "eks.amazonaws.com/role-arn=arn:aws:iam::640110193767:role/sri-eks-cluster-secrets-csi" --overwrite
kubectl apply -f https://raw.githubusercontent.com/aws/secrets-store-csi-driver-provider-aws/main/deployment/aws-provider-installer.yaml
```
* **Resultado:** DaemonSet `csi-secrets-store-provider-aws` y `secrets-store-csi-driver` en estado `3/3 Ready`.

### 4.5 Despliegue de AWS Load Balancer Controller (para Ingress / ALB)
```powershell
# 1. Aprovisionar Rol IAM y Política ALB en iac/aws/lb-controller
cd iac/aws/lb-controller
terraform init
terraform apply -auto-approve

# 2. Instalar el controlador en kube-system con Helm
kubectl create serviceaccount aws-load-balancer-controller -n kube-system --dry-run=client -o yaml | kubectl apply -f -
kubectl annotate serviceaccount aws-load-balancer-controller -n kube-system "eks.amazonaws.com/role-arn=arn:aws:iam::640110193767:role/sri-eks-cluster-alb-controller" --overwrite
helm repo add eks https://aws.github.io/eks-charts
helm repo update eks
helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller `
  -n kube-system `
  --set clusterName="sri-eks-cluster" `
  --set serviceAccount.create=false `
  --set serviceAccount.name="aws-load-balancer-controller" `
  --set region="us-east-1" `
  --set vpcId="vpc-04a09b3301d9e1955"
```
* **Resultado:** Deployment `aws-load-balancer-controller` en estado `2/2 Ready` en `kube-system`.

---

## 🔐 Fase 5: Inyección de Secretos y Publicación de Imágenes ECR

### 5.1 Parámetros en AWS Systems Manager Parameter Store
Se inyectaron en SSM los 3 secretos requeridos por la arquitectura desacoplada:
```powershell
aws ssm put-parameter --name "/sri-facturacion/SUPABASE_KEY" --value "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." --type "SecureString" --overwrite --region us-east-1
aws ssm put-parameter --name "/sri-facturacion/JWT_SECRET" --value "super-secret-key-cambiar-en-produccion" --type "SecureString" --overwrite --region us-east-1
aws ssm put-parameter --name "/sri-facturacion/FLASK_SECRET_KEY" --value "clave_secreta_frontend_aqui" --type "SecureString" --overwrite --region us-east-1
```

### 5.2 Compilación y Push de Imágenes Docker a ECR
*(Requiere tener Docker Desktop abierto en Windows)*:
```powershell
# 1. Login contra el registro ECR de AWS
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 640110193767.dkr.ecr.us-east-1.amazonaws.com

# 2. Compilar imágenes
docker build -t 640110193767.dkr.ecr.us-east-1.amazonaws.com/sri-backend:latest app/backend
docker build -t 640110193767.dkr.ecr.us-east-1.amazonaws.com/sri-frontend:latest app/frontend

# 3. Subir imágenes a ECR
docker push 640110193767.dkr.ecr.us-east-1.amazonaws.com/sri-backend:latest
docker push 640110193767.dkr.ecr.us-east-1.amazonaws.com/sri-frontend:latest
```

---

## 🚀 Fase 6: Despliegue GitOps con ArgoCD

Una vez publicadas las imágenes, se lanza la aplicación en el clúster EKS:
```powershell
kubectl apply -f gitops/argocd/project.yaml
kubectl apply -f gitops/argocd/application-aws-eks.yaml
```
ArgoCD tomará el control automático:
* Desplegará `sri-backend` (3 réplicas) y `sri-frontend` (3 réplicas).
* Montará los secretos vía CSI Driver desde SSM.
* El AWS Load Balancer Controller creará el ALB en AWS apuntando a los pods.

---

*(Fases 7 y 8 de Demo y Teardown se documentarán tras el despliegue).*
