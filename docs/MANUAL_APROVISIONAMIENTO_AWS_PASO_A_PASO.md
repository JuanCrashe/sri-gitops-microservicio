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
[FASE 1: PREPARACIÓN LOCAL & CREDENCIALES]   ✅ COMPLETADA
                        │
                        ▼
[FASE 2: RECURSOS BASE S3 / ECR]             ✅ COMPLETADA
                        │
                        ▼
[FASE 3: TERRAFORM APPLY (CLÚSTER EKS)]      ✅ COMPLETADA (9/9 RECURSOS - 3 NODOS READY)
                        │
                        ▼
[FASE 4: KUBECTL & CONTROLLERS (ALB/CSI)]    ✅ COMPLETADA (METRICS, ARGOCD, CSI, ALB)
                        │
                        ▼
[FASE 5: PARÁMETROS SSM & IMÁGENES ECR]      ✅ COMPLETADA (SECRETOS SSM & ECR IMAGES)
                        │
                        ▼
[FASE 6: GITOPS ARGOCD & APLICACIÓN EN VIVO] ✅ COMPLETADA (ALB ACTIVO & SYNCED)
                        │
                        ▼
[FASE 7: DEMO 5 MINUTOS & GRABACIÓN]         🎬 LISTA PARA GRABAR AHORA
                        │
                        ▼
[FASE 8: FINOPS TEARDOWN LIMPIO ($0.00/h)]   🛑 PROTOCOLO LISTO (EJECUTAR TRAS VIDEO)
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

## 🚀 Fase 6: Despliegue GitOps con ArgoCD (Completada)

### 6.1 Asegurar Contexto de Kubectl en EKS
Es fundamental verificar que el contexto apunte al clúster de AWS y no a Docker Desktop local:
```powershell
kubectl config use-context arn:aws:eks:us-east-1:640110193767:cluster/sri-eks-cluster
```

### 6.2 Aplicar Manifiestos de ArgoCD
```powershell
kubectl apply -f gitops/argocd/project.yaml
kubectl apply -f gitops/argocd/application-aws-eks.yaml
```

### 6.3 Verificación de Sincronización y Estado de Pods
```powershell
kubectl get application -n argocd sri-facturacion-aws-eks
kubectl get pods -n sri-facturacion -o wide
```
* **Estado Obtenido:**
  * **ArgoCD:** `Synced` y `Healthy`.
  * **Backend:** 3 réplicas en estado `1/1 Running` distribuidas entre los 3 nodos de EKS.
  * **Frontend:** 3 réplicas en estado `1/1 Running` distribuidas entre los 3 nodos de EKS.
  * **HPA:** `sri-backend-hpa` activo y monitoreando métricas con umbrales del 70% CPU y 80% RAM.

### 6.4 Obtención del DNS Público del Application Load Balancer (ALB)
```powershell
kubectl get ingress -n sri-facturacion
```
* **Salida Obtenida:**
```text
NAME                      CLASS   HOSTS               ADDRESS                                                                  PORTS   AGE
sri-facturacion-ingress   alb     api.sri.ec.gob.ec   k8s-srifactu-srifactu-a08031345f-400946508.us-east-1.elb.amazonaws.com   80      2m
```

### 6.5 Verificación de Salud en AWS ALB Target Groups
```powershell
# Verificar estado de los targets (Pods IP) en AWS
aws elbv2 describe-target-health --target-group-arn <FRONTEND_TG_ARN>
aws elbv2 describe-target-health --target-group-arn <BACKEND_TG_ARN>
```
* **Resultado:** Los 6 targets (3 frontend + 3 backend) se encuentran en estado `healthy`.

### 6.6 Pruebas de Conectividad End-to-End
```powershell
# 1. Probar carga del Frontend (Retorna HTTP 302 -> /login y renderiza el portal SRI)
curl.exe -I -s http://k8s-srifactu-srifactu-a08031345f-400946508.us-east-1.elb.amazonaws.com

# 2. Probar autenticación API mediante POST /api/v1/auth/login
curl.exe -s -X POST "http://k8s-srifactu-srifactu-a08031345f-400946508.us-east-1.elb.amazonaws.com/api/v1/auth/login" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=1790011674001&password=1234"

# 3. Probar consulta de contribuyente contra la base Supabase mediante el JWT generado
$token = (curl.exe -s -X POST "http://k8s-srifactu-srifactu-a08031345f-400946508.us-east-1.elb.amazonaws.com/api/v1/auth/login" -H "Content-Type: application/x-www-form-urlencoded" -d "username=1790011674001&password=1234" | ConvertFrom-Json).access_token
curl.exe -s -H "Authorization: Bearer $token" "http://k8s-srifactu-srifactu-a08031345f-400946508.us-east-1.elb.amazonaws.com/api/v1/contribuyente/1790011674001"
```
* **Respuesta JSON de Supabase en vivo:**
```json
{
  "ruc": "1790011674001",
  "razon_social": "CORPORACION FAVORITA C.A.",
  "estado_ruc": "ACTIVO",
  "tipo_contribuyente": "Sociedad",
  "regimen_impositivo": "Régimen General",
  "actividad_economica": "Venta al por mayor y menor de productos de supermercado...",
  "ultima_actualizacion": "2026-10-10T04:14:36.36294+00:00"
}
```

---

## 🎬 Fase 7: Guión de Grabación para la Defensa del TFM (5 Minutos)

El objetivo de este video es demostrar la orquestación real en AWS EKS, la entrega continua GitOps, la inyección segura de secretos y la alta disponibilidad.

### ⏱️ Cronograma Minuto a Minuto:

* **Minuto 0:00 - 1:00 | Introducción y Arquitectura en AWS:**
  * Mostrar terminal con los 3 nodos EKS corriendo en AWS:
    ```powershell
    kubectl get nodes -o wide
    ```
  * Mostrar que los nodos son instancias EC2 `t3.medium` en `us-east-1` ejecutando Kubernetes `v1.35.8`.
  * Explicar que la infraestructura fue declarada con Terraform y utiliza roles IAM con OIDC (IRSA).

* **Minuto 1:00 - 2:00 | GitOps con ArgoCD y Secretos CSI:**
  * Mostrar el estado de ArgoCD:
    ```powershell
    kubectl get application -n argocd sri-facturacion-aws-eks
    ```
  * Mostrar los pods en `sri-facturacion`:
    ```powershell
    kubectl get pods -n sri-facturacion -o wide
    ```
  * Explicar cómo el CSI Driver de AWS Secrets Store inyecta los secretos desde AWS Systems Manager Parameter Store directamente a memoria en los pods sin almacenar tokens en Git:
    ```powershell
    kubectl get secretproviderclass -n sri-facturacion
    ```

* **Minuto 2:00 - 3:30 | Demostración Web en Vivo (ALB Ingress):**
  * Abrir el navegador en la URL pública del Application Load Balancer:
    `http://k8s-srifactu-srifactu-a08031345f-400946508.us-east-1.elb.amazonaws.com`
  * Iniciar sesión en el portal SRI:
    * **RUC:** `1790011674001`
    * **Contraseña:** `1234`
  * Demostrar la consulta y visualización de la empresa **CORPORACION FAVORITA C.A.** conectada directamente a la persistencia PostgreSQL en Supabase.

* **Minuto 3:30 - 4:30 | Resiliencia y Autocuración (Self-Healing):**
  * En la terminal, simular la caída de un pod en caliente:
    ```powershell
    kubectl delete pod -n sri-facturacion -l app=sri-frontend --wait=false
    ```
  * Mostrar cómo Kubernetes y el ReplicaSet reemplazan inmediatamente el contenedor en segundos sin pérdida de servicio.

* **Minuto 4:30 - 5:00 | Conclusiones y Cumplimiento de Objetivos:**
  * Resaltar:
    1. Desacoplamiento total Frontend/Backend.
    2. Cero secretos en texto plano (Zero Trust).
    3. Entrega continua declarativa con GitOps.
    4. Portabilidad y preparación multicloud.

---

## 🛑 Fase 8: Protocolo de Destrucción Limpia FinOps ($0.00/h)

> [!CAUTION]
> **ORDEN CRÍTICO:** En AWS, si se destruye el clúster EKS antes de destruir el Ingress, el Application Load Balancer y los Security Groups dinámicos quedan **huérfanos**, generando cobros continuos en la factura. Siga estrictamente este orden.

### Paso 8.1: Eliminar Ingress y Aplicación ArgoCD (Desmantela el ALB)
```powershell
# 1. Eliminar la aplicación de ArgoCD
kubectl delete application -n argocd sri-facturacion-aws-eks --cascade=foreground

# 2. Asegurar la eliminación del Ingress
kubectl delete ingress -n sri-facturacion sri-facturacion-ingress --ignore-not-found=true

# 3. Eliminar el namespace de la aplicación
kubectl delete namespace sri-facturacion --ignore-not-found=true
```

### Paso 8.2: Verificar que el Load Balancer fue eliminado en AWS
```powershell
# Debe retornar una tabla vacía una vez desaprovisionado el ALB
aws elbv2 describe-load-balancers --query "LoadBalancers[*].[LoadBalancerName,State.Code]" --output table
```

### Paso 8.3: Destruir Controladores Helm
```powershell
$env:PATH += ";C:\Users\ASUS\AppData\Local\Microsoft\WinGet\Packages\Helm.Helm_Microsoft.Winget.Source_8wekyb3d8bbwe\windows-amd64"
helm uninstall aws-load-balancer-controller -n kube-system
helm uninstall secrets-store-csi-driver -n kube-system
```

### Paso 8.4: Destruir Infraestructura con Terraform
Ejecutar `terraform destroy` en orden inverso de dependencias:

```powershell
# 1. Destruir IAM y configuraciones de Load Balancer Controller
cd "c:\Users\ASUS\Documents\Papi\Maestria DevOps UNIR\TFM\microservicio\sri-gitops-microservicio\iac\aws\lb-controller"
terraform destroy -auto-approve

# 2. Destruir IAM y recursos de Secrets CSI
cd "c:\Users\ASUS\Documents\Papi\Maestria DevOps UNIR\TFM\microservicio\sri-gitops-microservicio\iac\aws\secrets-csi"
terraform destroy -auto-approve

# 3. Destruir el Clúster EKS y los Nodos Workers
cd "c:\Users\ASUS\Documents\Papi\Maestria DevOps UNIR\TFM\microservicio\sri-gitops-microservicio\iac\aws"
terraform destroy -auto-approve
```

### Paso 8.5: Limpiar Parámetros SSM (Opcional si se desea borrar secretos)
```powershell
aws ssm delete-parameters --names "/sri-facturacion/SUPABASE_KEY" "/sri-facturacion/JWT_SECRET" "/sri-facturacion/FLASK_SECRET_KEY" --region us-east-1
```

### Paso 8.6: Verificación Final de Facturación Cero en AWS
```powershell
# 1. Verificar instancias EC2 (deben estar todas en 'terminated')
aws ec2 describe-instances --query "Reservations[*].Instances[*].[InstanceId,State.Name]" --output table

# 2. Verificar clústeres EKS (debe retornar vacío)
aws eks list-clusters --output table

# 3. Verificar Load Balancers (debe retornar vacío)
aws elbv2 describe-load-balancers --output table
```
Al finalizar este procedimiento, el consumo horario en la cuenta AWS vuelve a **$0.00/h**.
