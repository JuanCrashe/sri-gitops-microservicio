# 📘 Manual Operativo Multicloud: Guía Paso a Paso de Despliegue (Local, AWS y Azure)

**Proyecto:** GitOps Multicloud: Implementación de Pipelines CI/CD con Infraestructura como Código Agnóstica para la Portabilidad de Microservicios  
**Máster:** MUDEVOPS — UNIR  
**Propósito:** Guía de ejecución y manual de procedimientos para desplegar, validar y destruir el microservicio de facturación del SRI en tres entornos heterogéneos: **Local (Docker Desktop)**, **AWS (Amazon EKS)** y **Azure (Azure AKS)**.

---

## 📑 Tabla de Contenidos

1. [Matriz Comparativa de Ambientes](#1-matriz-comparativa-de-ambientes)
2. [Ambiente 1: Despliegue Local (Docker Desktop / Kind)](#2-ambiente-1-despliegue-local-docker-desktop--kind)
   - [2.1 Prerrequisitos y Verificación](#21-prerrequisitos-y-verificación)
   - [2.2 Paso 1: Construcción de Imágenes Docker Locales](#22-paso-1-construcción-de-imágenes-docker-locales)
   - [2.3 Paso 2: Instalación de ArgoCD en el Clúster](#23-paso-2-instalación-de-argocd-en-el-clúster)
   - [2.4 Paso 3: Aprovisionamiento de Secretos y Configuración](#24-paso-3-aprovisionamiento-de-secretos-y-configuración)
   - [2.5 Paso 4: Despliegue GitOps de la Aplicación (Kustomize Local)](#25-paso-4-despliegue-gitops-de-la-aplicación-kustomize-local)
   - [2.6 Paso 5: Despliegue del Stack de Observabilidad Ligero (Prometheus + Grafana)](#26-paso-5-despliegue-del-stack-de-observabilidad-ligero-prometheus--grafana)
   - [2.7 Paso 6: Verificación de Salud, Portales y Métricas DORA](#27-paso-6-verificación-de-salud-portales-y-métricas-dora)
   - [2.8 Paso 7: Limpieza y Teardown Local](#28-paso-7-limpieza-y-teardown-local)
3. [Ambiente 2: Despliegue en AWS (Amazon EKS)](#3-ambiente-2-despliegue-en-aws-amazon-eks)
   - [3.1 Prerrequisitos y Configuración de Identidad (IAM)](#31-prerrequisitos-y-configuración-de-identidad-iam)
   - [3.2 Fase 0: Plataforma Base de Larga Vida (S3 Backend, ECR y OIDC)](#32-fase-0-plataforma-base-de-larga-vida-s3-backend-ecr-y-oidc)
   - [3.3 Fase 1: Aprovisionamiento de Infraestructura con Terraform (IaC)](#33-fase-1-aprovisionamiento-de-infraestructura-con-terraform-iac)
   - [3.4 Fase 2: Configuración del Clúster EKS y Addons Esenciales](#34-fase-2-configuración-del-clúster-eks-y-addons-esenciales)
   - [3.5 Fase 3: Despliegue GitOps con ArgoCD (Overlay AWS)](#35-fase-3-despliegue-gitops-con-argocd-overlay-aws)
   - [3.6 Fase 4: Despliegue del Stack de Observabilidad en EKS](#36-fase-4-despliegue-del-stack-de-observabilidad-en-eks)
   - [3.7 Fase 5: Verificación Ingress (ALB), Escalado y Telemetría](#37-fase-5-verificación-ingress-alb-escalado-y-telemetría)
   - [3.8 Fase 6: FinOps y Destrucción Limpia en AWS ($0/h)](#38-fase-6-finops-y-destrucción-limpia-en-aws-0h)
4. [Ambiente 3: Despliegue en Azure (Azure AKS)](#4-ambiente-3-despliegue-en-azure-azure-aks)
   - [4.1 Prerrequisitos y Autenticación con Azure CLI](#41-prerrequisitos-y-autenticación-con-azure-cli)
   - [4.2 Fase 0: Plataforma Base de Larga Vida (Storage Account, ACR y RBAC)](#42-fase-0-plataforma-base-de-larga-vida-storage-account-acr-y-rbac)
   - [4.3 Fase 1: Aprovisionamiento de AKS con Terraform (Módulo Agnóstico)](#43-fase-1-aprovisionamiento-de-aks-con-terraform-módulo-agnóstico)
   - [4.4 Fase 2: Configuración del Clúster AKS y Addons](#44-fase-2-configuración-del-clúster-aks-y-addons)
   - [4.5 Fase 3: Despliegue GitOps con ArgoCD (Overlay Azure)](#45-fase-3-despliegue-gitops-con-argocd-overlay-azure)
   - [4.6 Fase 4: Despliegue del Stack de Observabilidad en AKS](#46-fase-4-despliegue-del-stack-de-observabilidad-en-aks)
   - [4.7 Fase 5: Verificación de IP Pública, Tráfico y Telemetría](#47-fase-5-verificación-de-ip-pública-tráfico-y-telemetría)
   - [4.8 Fase 6: FinOps y Destrucción Limpia en Azure ($0/h)](#48-fase-6-finops-y-destrucción-limpia-en-azure-0h)
5. [Guía Rápida de Troubleshooting y Mitigación de Errores](#5-guía-rápida-de-troubleshooting-y-mitigación-de-errores)

---

## 1. Matriz Comparativa de Ambientes

El principio rector de la arquitectura es la **portabilidad declarativa**: el microservicio se define en manifiestos base inmutables (`gitops/bases/`), y Kustomize inyecta las variaciones específicas de cada nube mediante overlays:

| Característica / Capa | Ambiente Local | Ambiente AWS (EKS) | Ambiente Azure (AKS) |
| :--- | :--- | :--- | :--- |
| **Orquestador** | Docker Desktop (K8s v1.32+) | Amazon EKS v1.30 (Managed NodeGroup) | Azure AKS v1.30 (System Pool) |
| **Infraestructura (IaC)** | N/A (Docker Desktop GUI / Kind) | Terraform `iac/aws` (VPC, Subnets, EKS, IAM) | Terraform `iac/azure` (RG, AKS, VNet) |
| **Container Registry** | Local Docker Engine (`sri-*:latest`) | Amazon ECR (`053044806920.dkr.ecr...`) | Azure ACR (`sriacrtfm23c5.azurecr.io`) |
| **Gestión de Secretos** | Secret nativo de K8s (`sri-db-secret`) | AWS SSM Parameter Store + CSI Driver | Azure Key Vault + Secrets Store CSI |
| **Ingress / Exposición** | Port-forwarding / LoadBalancer localhost | AWS Load Balancer Controller (ALB) | Azure Application Gateway / LoadBalancer IP |
| **GitOps Engine** | ArgoCD (namespace `argocd`) | ArgoCD (namespace `argocd`) | ArgoCD (namespace `argocd`) |
| **Observabilidad** | Prometheus + Grafana (PVC 2Gi ligero) | Prometheus Operator + Grafana (20Gi EBS) | Prometheus Operator + Grafana (20Gi AzureDisk) |
| **Costo Operativo** | **$0.00** (Hardware local) | **~$0.22/h** (~$0.80 - $1.20 demo completa) | **~$0.20/h** (~$0.70 - $1.10 demo completa) |

---

## 2. Ambiente 1: Despliegue Local (Docker Desktop / Kind)

Este ambiente permite reproducir el 100% de la funcionalidad del microservicio, autosanación GitOps, elasticidad HPA y observabilidad con costo cero sin depender de conexión a nubes públicas.

### 2.1 Prerrequisitos y Verificación
* **Docker Desktop:** Instalado con Kubernetes activado en *Settings > Kubernetes > Enable Kubernetes*.
* **Herramientas CLI:** `docker`, `kubectl`, `git`, `curl` (o PowerShell en Windows).

Verificar conectividad con el clúster local:
```bash
kubectl cluster-info
```
* **Significado del comando:** Consulta al API Server de Kubernetes la URL del plano de control y servicios centrales.
* **Qué hace:** Confirma que el cliente `kubectl` tiene contexto apuntando a `docker-desktop` y que el clúster está respondiendo.

Verificar StorageClass local por defecto:
```bash
kubectl get storageclass
```
* **Significado del comando:** Lista los aprovisionadores de almacenamiento persistente registrados.
* **Qué hace:** Verifica que existe `standard (default)` (respaldado por `hostpath` o `rancher.io/local-path`), indispensable para el PVC de Prometheus.

---

### 2.2 Paso 1: Construcción de Imágenes Docker Locales

Dado que en local no se usa un registry remoto con autenticación OIDC, se construyen las imágenes etiquetadas como `:latest` directamente en el Docker daemon del host:

```bash
# Construir imagen del Backend (FastAPI + psycopg2 + Supabase client)
docker build -t sri-backend:latest -f app/backend/Dockerfile app/backend
```
* **Significado de flags:**
  * `-t sri-backend:latest`: Asigna el nombre y tag de la imagen resultante.
  * `-f app/backend/Dockerfile`: Ruta específica al Dockerfile que compilará el código de FastAPI.
  * `app/backend`: Contexto de construcción (archivos que se envían al daemon de Docker).
* **Qué hace:** Instala dependencias (`requirements.txt`), compila paquetes C (`libpq-dev`, `gcc`), copia el código y empaqueta la imagen del backend.

```bash
# Construir imagen del Frontend (Flask + Jinja2 + Bootstrap 5)
docker build -t sri-frontend:latest -f app/frontend/Dockerfile app/frontend
```
* **Significado de flags:** Igual que el anterior, aplicado a la aplicación Flask.
* **Qué hace:** Genera la imagen web que renderiza las vistas institucionales y gestiona sesiones con tokens JWT.

Verificar imágenes compiladas:
```bash
docker images | grep sri-
```
* **Qué hace:** Valida que ambas imágenes (`sri-backend` y `sri-frontend`) residen en el motor local y están listas para ser instanciadas por Kubernetes sin necesidad de `imagePullSecrets`.

---

### 2.3 Paso 2: Instalación de ArgoCD en el Clúster

ArgoCD actúa como el operador GitOps que sincroniza el estado del clúster con el repositorio Git.

```bash
# Crear namespace aislado para ArgoCD
kubectl create namespace argocd
```
* **Qué hace:** Crea el espacio de nombres lógico `argocd` donde se confinarán los controladores y la interfaz gráfica de GitOps.

```bash
# Instalar los manifiestos oficiales estables de ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v2.11.0/manifests/install.yaml
```
* **Significado de flags:**
  * `-n argocd`: Limita la aplicación de los objetos al namespace `argocd`.
  * `-f <URL>`: Aplica directamente la colección de Deployments, Services, CRDs, Roles y ServiceAccounts oficiales.
* **Qué hace:** Despliega `argocd-server`, `argocd-repo-server`, `argocd-application-controller`, Redis y Dex.

Esperar a que todos los componentes de ArgoCD estén en ejecución:
```bash
kubectl wait --for=condition=Available deployment/argocd-server -n argocd --timeout=300s
```
* **Significado de flags:**
  * `--for=condition=Available`: Bloquea la consola hasta que el Deployment alcance réplicas saludables.
  * `--timeout=300s`: Establece un límite de espera de 5 minutos antes de abortar.

Exponer la interfaz web de ArgoCD localmente:
```bash
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'
```
* **Significado de flags:**
  * `patch svc ...`: Modifica la definición en caliente del servicio de Kubernetes.
  * `-p '{"spec": {"type": "LoadBalancer"}}'`: Cambia el tipo de servicio de `ClusterIP` a `LoadBalancer`.
* **Qué hace:** Permite que Docker Desktop enlace automáticamente el servicio HTTPS a `https://localhost` (puerto 443).

Obtener la contraseña inicial de administración (`admin`):
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String((Get-Clipboard -Raw)))
```
*(En bash / Linux usar: `kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d`)*
* **Qué hace:** Extrae la clave secreta autogenerada por ArgoCD y la decodifica de Base64 para permitir el primer inicio de sesión.

---

### 2.4 Paso 3: Aprovisionamiento de Secretos y Configuración

El backend requiere credenciales para comunicarse con la base de datos PostgreSQL alojada en Supabase. En local se inyecta un Secret nativo:

```bash
# Crear namespace de la aplicación
kubectl create namespace sri-facturacion --dry-run=client -o yaml | kubectl apply -f -
```
* **Qué hace:** Crea el namespace de negocio `sri-facturacion` de forma idempotente (sin fallar si ya existe).

```bash
# Crear Secret con las credenciales de la base de datos Supabase
kubectl create secret generic sri-db-secret \
  --namespace sri-facturacion \
  --from-literal=DB_HOST="aws-0-us-east-1.pooler.supabase.com" \
  --from-literal=DB_PORT="6543" \
  --from-literal=DB_NAME="postgres" \
  --from-literal=DB_USER="postgres.jtuqawnhrvtquhyjkluh" \
  --from-literal=DB_PASSWORD="TU_PASSWORD_AQUI" \
  --from-literal=JWT_SECRET_KEY="sri_devops_secret_key_2026_super_segura" \
  --dry-run=client -o yaml | kubectl apply -f -
```
* **Significado de flags:**
  * `generic sri-db-secret`: Crea un secreto de tipo genérico/Opaque.
  * `--from-literal=CLAVE=VALOR`: Define cada variable sensible que el backend y frontend mapearán como variables de entorno.
  * `--dry-run=client -o yaml | kubectl apply -f -`: Patrón declarativo que previene errores de recurso duplicado.

---

### 2.5 Paso 4: Despliegue GitOps de la Aplicación (Kustomize Local)

```bash
# 1. Configurar el AppProject con permisos de clúster
kubectl apply -f gitops/argocd/project.yaml
```
* **Qué hace:** Registra el proyecto de ArgoCD `sri-facturacion`, autorizando los repositorios de GitHub, el repositorio de Helm de Prometheus y los namespaces de destino permitidos (`sri-facturacion`, `monitoring`, `argocd`, `kube-system`).

```bash
# 2. Desplegar la Aplicación GitOps local
kubectl apply -f gitops/argocd/application-local.yaml
```
* **Qué hace:** Registra el objeto `Application` en ArgoCD. El controlador clonará el repositorio Git, compilará el overlay `gitops/overlays/local` mediante Kustomize y desplegará los Deployments, Services y el HPA.

Verificar el estado de la sincronización en ArgoCD:
```bash
kubectl get application sri-facturacion-local -n argocd
```
* **Salida esperada:** `SYNC STATUS: Synced`, `HEALTH STATUS: Healthy`.

Comprobar que los pods de negocio están corriendo:
```bash
kubectl get pods -n sri-facturacion
```
* **Salida esperada:** 3 pods de `sri-backend` en estado `Running` (1/1) y 2 pods de `sri-frontend` en estado `Running` (1/1).

---

### 2.6 Paso 5: Despliegue del Stack de Observabilidad Ligero (Prometheus + Grafana)

Para cumplir con el requerimiento de evaluación de métricas DORA sin agotar los recursos locales, se usa el archivo de valores optimizado [values-local.yaml](file:///c:/Users/ASUS/Documents/Papi/Maestria%20DevOps%20UNIR/TFM/microservicio/sri-gitops-microservicio/gitops/monitoring/values-local.yaml) que reserva un PVC de solo **2Gi**.

```bash
# Desplegar la aplicación de observabilidad mediante ArgoCD Multi-Source
kubectl apply -f gitops/argocd/application-monitor-local.yaml
```
* **Qué hace:** Instruye a ArgoCD a descargar el Chart Helm oficial `kube-prometheus-stack` (v61.3.0) desde `https://prometheus-community.github.io/helm-charts` y aplicar sobre él la configuración local del repo `$values/gitops/monitoring/values-local.yaml`.

Monitorear el arranque de los pods de observabilidad:
```bash
kubectl get pods -n monitoring -w
```
* **Salida esperada:**
  * `prometheus-sri-monitoring-prometheus-0` (2/2 Running)
  * `sri-monitor-local-grafana-*` (3/3 Running)
  * `sri-monitor-local-kube-state-metrics-*` (1/1 Running)
  * `sri-monitor-local-prometheus-node-exporter-*` (1/1 Running)
  * `sri-monitoring-operator-*` (1/1 Running)

Verificar el volumen persistente (PVC) ligero:
```bash
kubectl get pvc -n monitoring
```
* **Salida esperada:** Volumen en estado `Bound` con capacidad exacta de `2Gi`.

Importar el Dashboard de Métricas DORA en Grafana vía API REST:
```powershell
$pair = "admin:prom-operator"
$bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
$base64 = [Convert]::ToBase64String($bytes)
$body = Get-Content -Raw "gitops/monitoring/dashboard-dora.json"
Invoke-RestMethod -Uri "http://localhost:3000/api/dashboards/db" -Method Post -Body $body -ContentType "application/json" -Headers @{ Authorization = "Basic $base64" }
```
*(En bash / Linux):*
```bash
curl -X POST -H "Content-Type: application/json" -u admin:prom-operator \
  http://localhost:3000/api/dashboards/db -d @gitops/monitoring/dashboard-dora.json
```
* **Qué hace:** Registra declarativamente el panel de control con métricas DORA (Deployment Frequency, Change Failure Rate, MTTR y Disponibilidad) dentro de Grafana.

---

### 2.7 Paso 6: Verificación de Salud, Portales y Métricas DORA

Comprobar que todas las URLs locales responden exitosamente:

| Servicio / Portal | URL Local | Credenciales | Verificación |
| :--- | :--- | :--- | :--- |
| **Frontend Web SRI** | [http://localhost:8088](http://localhost:8088) | `admin@sri.gob.ec` / `Admin2026*` | Login, consulta y actualización de RUC |
| **Backend REST API** | [http://localhost:5000/health](http://localhost:5000/health) | N/A | Retorna `{"status": "healthy"}` |
| **Versión Multi-cloud** | [http://localhost:5000/api/v1/version](http://localhost:5000/api/v1/version) | N/A | Retorna `cloud: "local-docker-desktop"` |
| **ArgoCD Dashboard** | [https://localhost](https://localhost) | `admin` / *(clave del paso 2.3)* | Estado `Synced` de ambas aplicaciones |
| **Grafana Observabilidad**| [http://localhost:3000](http://localhost:3000) | `admin` / `prom-operator` | Métricas DORA y telemetría de pods |

Probar la respuesta del backend desde terminal:
```bash
curl -s http://localhost:5000/api/v1/version
```
* **Qué hace:** Realiza una petición GET al endpoint agnóstico validando que el pod responde e identifica correctamente su entorno local.

---

### 2.8 Paso 7: Limpieza y Teardown Local

Para liberar memoria y disco en el equipo de desarrollo cuando finalice la sesión:

```bash
# Eliminar aplicaciones de ArgoCD (elimina los pods de sri-facturacion y monitoring)
kubectl delete application sri-monitor-local -n argocd
kubectl delete application sri-facturacion-local -n argocd

# Eliminar namespaces y almacenamiento persistente
kubectl delete namespace sri-facturacion
kubectl delete namespace monitoring

# (Opcional) Eliminar ArgoCD
kubectl delete namespace argocd
```
* **Qué hace:** Elimina todos los recursos instanciados, libera los puertos `8088`, `5000`, `3000` y `443`, y destruye el PVC de 2Gi del disco local.

---

## 3. Ambiente 2: Despliegue en AWS (Amazon EKS)

Este procedimiento provisiona un clúster gestionado de **Amazon EKS** de grado productivo utilizando Terraform, integrando el registro privado **Amazon ECR**, secretos mediante **AWS Systems Manager Parameter Store + Secrets Store CSI**, y balanceo de carga L7 mediante **AWS Load Balancer Controller (ALB)**.

### 3.1 Prerrequisitos y Configuración de Identidad (IAM)

* **Herramientas obligatorias en la máquina de ejecución:**
  * `terraform >= 1.8.0`
  * `aws-cli v2`
  * `kubectl >= 1.30`
  * `helm >= 3.14`
* **Credenciales de AWS:** Cuenta configurada con el usuario IAM de menor privilegio `terraform-ci` (definido en el proyecto) o credenciales de administrador:

```bash
aws configure
```
* **Significado de las preguntas del asistente:**
  * `AWS Access Key ID`: Clave de acceso pública del usuario IAM.
  * `AWS Secret Access Key`: Clave secreta asociada.
  * `Default region name`: `us-east-1` (región oficial del proyecto).
  * `Default output format`: `json`.

Verificar identidad activa:
```bash
aws sts get-caller-identity
```
* **Qué hace:** Realiza una llamada a AWS Security Token Service (STS) retornando el `Account`, `UserId` y `Arn` activo, garantizando que los comandos subsiguientes no fallarán por falta de credenciales.

---

### 3.2 Fase 0: Plataforma Base de Larga Vida (S3 Backend, ECR y OIDC)

> [!NOTE]
> Estos componentes se crean **UNA sola vez** en la cuenta y sobreviven a todos los ciclos de destrucción y recreación del clúster EKS para mantener costo $0 cuando no se usa.

#### Paso 0.1: Bucket S3 de Estado Remoto y DynamoDB para State Locking
```bash
bash scripts/bootstrap-backend-aws.sh
```
* **Comandos internos que ejecuta:**
  * `aws s3api create-bucket --bucket sri-gitops-tfstate --region us-east-1`: Crea el bucket de almacenamiento seguro.
  * `aws s3api put-bucket-versioning ...`: Habilita versionado para proteger el archivo `terraform.tfstate` ante corrupciones.
  * `aws s3api put-bucket-encryption ...`: Encripta el estado en reposo con AES-256.
  * `aws s3api put-public-access-block ...`: Bloquea cualquier acceso público accidental.
  * `aws dynamodb create-table --table-name sri-gitops-tflocks ...`: Crea la tabla para evitar que dos ejecuciones concurrentes de Terraform modifiquen el estado simultáneamente.

#### Paso 0.2: Registro Privado de Contenedores (Amazon ECR)
```bash
cd iac/aws/registry
terraform init
terraform apply -auto-approve
cd ../../..
```
* **Significado de flags:**
  * `terraform init`: Descarga el provider oficial de AWS en el directorio local.
  * `terraform apply -auto-approve`: Aplica los cambios sin requerir confirmación interactiva por teclado.
* **Qué hace:** Crea el repositorio `sri-facturacion-service` en ECR con escaneo de vulnerabilidades al subir (`scan_on_push = true`) y regla de ciclo de vida para retener las últimas 10 imágenes. Posee `prevent_destroy = true` para evitar borrados accidentales.

#### Paso 0.3: Federación OIDC para GitHub Actions (CI/CD sin claves estáticas)
```bash
bash scripts/bootstrap-github-oidc-aws.sh
```
* **Qué hace:** Registra `token.actions.githubusercontent.com` como Identity Provider OIDC en IAM y crea el rol `github-actions-ecr-push` con una política de confianza estricta hacia el repositorio `JuanCrashe/sri-gitops-microservicio`, permitiendo que el workflow compile y publique imágenes en ECR sin almacenar secretos permanentes en GitHub.

---

### 3.3 Fase 1: Aprovisionamiento de Infraestructura con Terraform (IaC)

#### Paso 1.1: Preparar archivo de variables
```bash
cd iac/aws
cp terraform.tfvars.example terraform.tfvars
```
* **Qué hace:** Crea el archivo local de variables (ignorado por `.gitignore`). Si se utiliza una cuenta AWS normal, los campos `cluster_role_arn` y `node_role_arn` se dejan vacíos para que Terraform los cree automáticamente con permisos de menor privilegio.

#### Paso 1.2: Inicialización y Validación
```bash
terraform init
```
* **Qué hace:** Configura el backend remoto en el bucket S3 `sri-gitops-tfstate` y la tabla DynamoDB `sri-gitops-tflocks`.

```bash
terraform validate
```
* **Qué hace:** Revisa estáticamente la sintaxis de los archivos HCL y la consistencia de tipos entre variables y salidas.

#### Paso 1.3: Plan y Despliegue del Clúster EKS
```bash
terraform plan -out=tfplan
```
* **Significado de flags:**
  * `-out=tfplan`: Guarda el plan de ejecución binario para asegurar que se aplique exactamente lo calculado.
* **Qué hace:** Calcula el delta entre la nube y el código. Debe indicar **11 recursos a agregar** (VPC, Subnets públicas/privadas, Internet Gateway, NAT Gateway, Security Groups, EKS Control Plane y NodeGroup gestionado).

```bash
terraform apply tfplan
cd ../..
```
* **Qué hace:** Ejecuta el aprovisionamiento real en AWS (duración aproximada: 12 a 15 minutos). Al concluir, retorna los outputs con el Endpoint del clúster, el OIDC Issuer URL y el nombre del clúster `sri-eks-cluster`.

---

### 3.4 Fase 2: Configuración del Clúster EKS y Addons Esenciales

#### Paso 2.1: Actualizar Kubeconfig local
```bash
aws eks update-kubeconfig --name sri-eks-cluster --region us-east-1
```
* **Significado de flags:**
  * `--name sri-eks-cluster`: Nombre exacto del clúster en EKS.
  * `--region us-east-1`: Región geográfica donde opera.
* **Qué hace:** Descarga el certificado CA y el endpoint del clúster, configurando el contexto activo de `kubectl` con autenticación delegada vía `aws-iam-authenticator`.

Verificar que los 3 nodos trabajadores están operativos:
```bash
kubectl get nodes
```
* **Salida esperada:** 3 nodos en estado `Ready`.

#### Paso 2.2: Desplegar Metrics Server (Requerimiento vital para el HPA)
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```
* **Qué hace:** Instala el agente ligero que recolecta métricas de CPU y memoria desde los kubelets. Sin este componente, el Horizontal Pod Autoscaler (HPA) entra en estado `<unknown>` y no puede escalar.

Verificar funcionamiento:
```bash
kubectl top nodes
```
* **Qué hace:** Consulta las métricas en tiempo real reportando uso de CPU en cores y memoria en bytes por nodo.

#### Paso 2.3: Instalar ArgoCD en EKS
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v2.11.0/manifests/install.yaml
kubectl wait --for=condition=Available deployment/argocd-server -n argocd --timeout=300s
```
* **Qué hace:** Inicializa el plano de control de GitOps dentro del clúster EKS.

#### Paso 2.4: Aprovisionar Secrets Store CSI Driver + AWS Provider
```bash
# 1. Aprovisionar el rol IAM para CSI con Terraform
cd iac/aws/secrets-csi
terraform init
terraform apply -auto-approve
cd ../../..

# 2. Instalar el driver CSI en Kubernetes vía script automatizado
bash scripts/bootstrap-secrets-csi-eks.sh
```
* **Qué hace:**
  1. Terraform crea la política IAM con permisos `ssm:GetParameter` y la asocia al rol IRSA (IAM Roles for Service Accounts) usando el OIDC provider del clúster.
  2. El script Helm instala el `secrets-store-csi-driver` en `kube-system` con sincronización a Secrets nativos (`syncSecret.enabled=true`) y monta el daemonset del proveedor AWS.

#### Paso 2.5: Instalar AWS Load Balancer Controller
```bash
# 1. Aprovisionar rol IAM y política oficial de ALB
cd iac/aws/lb-controller
terraform init
terraform apply -auto-approve
cd ../../..

# 2. Instalar el controller mediante Helm
bash scripts/bootstrap-lb-controller-eks.sh
```
* **Qué hace:** Instala el controlador de Kubernetes que escucha objetos de tipo `Ingress` con `ingressClassName: alb` y aprovisiona de forma declarativa un Application Load Balancer (ALB) en AWS con sus respectivos Target Groups y Listeners.

---

### 3.5 Fase 3: Despliegue GitOps con ArgoCD (Overlay AWS)

```bash
# 1. Registrar el AppProject sri-facturacion en el clúster EKS
kubectl apply -f gitops/argocd/project.yaml

# 2. Aplicar la definición de la Aplicación para AWS
kubectl apply -f gitops/argocd/application-aws-eks.yaml
```
* **Qué hace:** ArgoCD detecta la aplicación, lee la ruta `gitops/overlays/aws-eks` de Git, aplica los parches de Kustomize específicos de AWS:
  * Inyecta la imagen desde ECR (`053044806920.dkr.ecr.us-east-1.amazonaws.com/sri-facturacion-service`).
  * Inyecta el objeto `SecretProviderClass` conectado al Parameter Store de AWS.
  * Crea el recurso `Ingress` que desencadena la creación del ALB público.

Verificar el despliegue:
```bash
kubectl get application sri-facturacion-aws-eks -n argocd
```
* **Salida esperada:** `Synced` y `Healthy`.

---

### 3.6 Fase 4: Despliegue del Stack de Observabilidad en EKS

```bash
kubectl apply -f gitops/argocd/application-monitor-aws.yaml
```
* **Qué hace:** Despliega `kube-prometheus-stack` en el namespace `monitoring` de EKS consumiendo [gitops/monitoring/values.yaml](file:///c:/Users/ASUS/Documents/Papi/Maestria%20DevOps%20UNIR/TFM/microservicio/sri-gitops-microservicio/gitops/monitoring/values.yaml). Provisiona un volumen persistente de **20Gi** respaldado por volúmenes EBS GP3 mediante el CSI Driver de almacenamiento de AWS.

---

### 3.7 Fase 5: Verificación Ingress (ALB), Escalado y Telemetría

Obtener la URL pública del Application Load Balancer creado por AWS:
```bash
kubectl get ingress sri-ingress -n sri-facturacion -o jsonpath="{.status.loadBalancer.ingress[0].hostname}"
```
* **Qué hace:** Recupera el DNS público asignado por AWS (ej. `k8s-srifactu-sriingre-xxxxxxxxxx.us-east-1.elb.amazonaws.com`).

Probar tráfico y respuesta del microservicio en AWS:
```bash
curl -I http://<ALB-HOSTNAME>/
curl -s http://<ALB-HOSTNAME>/api/v1/version
```
* **Salida esperada en `/api/v1/version`:**
```json
{
  "version": "1.0.0",
  "cloud": "aws",
  "cluster": "sri-eks-cluster",
  "hostname": "sri-backend-xxxxxxxxxx"
}
```

Acceder a Grafana en AWS mediante port-forwarding seguro:
```bash
kubectl port-forward svc/sri-monitoring-grafana 3000:80 -n monitoring
```
* **Qué hace:** Crea un túnel SSH/TLS entre el puerto local 3000 y el servicio interno de Grafana en EKS. Abrir [http://localhost:3000](http://localhost:3000) en el navegador.

---

### 3.8 Fase 6: FinOps y Destrucción Limpia en AWS ($0/h)

> [!CAUTION]
> **Regla de Oro FinOps:** Para evitar costos continuos en la nube, el Application Load Balancer (ALB) **DEBE eliminarse ANTES** de destruir el clúster. Si se destruye el clúster primero, el ALB queda huérfano en AWS y continuará facturando.

#### Paso 6.1: Eliminar Aplicaciones GitOps y el Ingress (ALB)
```bash
# 1. Eliminar aplicaciones de ArgoCD
kubectl delete application sri-monitor-aws-eks -n argocd --cascade=foreground
kubectl delete application sri-facturacion-aws-eks -n argocd --cascade=foreground

# 2. Garantizar que el Ingress y el ALB han sido completamente retirados de AWS
kubectl delete ingress sri-ingress -n sri-facturacion --ignore-not-found=true
```
* **Qué hace:** Espera a que el AWS Load Balancer Controller desaprovisione el ALB en AWS y elimine los Target Groups.

Verificar que no quedan balanceadores huérfanos:
```bash
aws elbv2 describe-load-balancers --query "LoadBalancers[?contains(LoadBalancerName, 'sri')].LoadBalancerArn" --output text
```
* **Salida esperada:** Cadena vacía (sin balanceadores activos).

#### Paso 6.2: Destruir Addons de Terraform
```bash
# Destruir AWS Load Balancer Controller IAM
cd iac/aws/lb-controller
terraform destroy -auto-approve

# Destruir Secrets CSI IAM
cd ../secrets-csi
terraform destroy -auto-approve
cd ../../..
```

#### Paso 6.3: Destruir el Clúster EKS y la VPC
```bash
cd iac/aws
terraform destroy -auto-approve
cd ../..
```
* **Qué hace:** Destruye los 11 recursos de cómputo y red (Control Plane de EKS, Node Group EC2, NAT Gateway, Internet Gateway y VPC). Al terminar, la facturación del clúster pasa a **$0.00/h**.
* **Recursos preservados:** El bucket S3 (`sri-gitops-tfstate`), el repositorio ECR y el OIDC de GitHub no se tocan para poder recrear el clúster en cualquier momento en 12 minutos.

---

## 4. Ambiente 3: Despliegue en Azure (Azure AKS)

Este procedimiento provisiona un clúster gestionado de **Azure Kubernetes Service (AKS)** utilizando el módulo agnóstico de Terraform, integrando **Azure Container Registry (ACR)** con autenticación Entra ID, secretos centralizados mediante **Azure Key Vault + Secrets Store CSI** y observabilidad declarativa con ArgoCD.

### 4.1 Prerrequisitos y Autenticación con Azure CLI

* **Herramientas obligatorias:**
  * `terraform >= 1.8.0`
  * `az-cli` (Azure CLI)
  * `kubectl >= 1.30`
  * `helm >= 3.14`

Iniciar sesión interactiva en la suscripción de Azure:
```bash
az login
```
* **Qué hace:** Abre el navegador web para autenticar con la cuenta institucional de Microsoft Entra ID y descarga el token de acceso local.

Establecer la suscripción de trabajo:
```bash
az account set --subscription "TU_SUBSCRIPTION_ID_O_NOMBRE"
```
* **Significado de flags:**
  * `--subscription`: Selecciona explícitamente el Tenant/Suscripción sobre el cual se aplicará la infraestructura.

Verificar cuenta activa:
```bash
az account show --output table
```
* **Qué hace:** Muestra la tabla con el `Name`, `SubscriptionId`, `TenantId` y el estado `Enabled`.

---

### 4.2 Fase 0: Plataforma Base de Larga Vida (Storage Account, ACR y RBAC)

Al igual que en AWS, estos recursos constituyen la plataforma base y sobreviven al ciclo de vida del clúster AKS.

#### Paso 0.1: Resource Group y Storage Account para Terraform State
```bash
bash scripts/bootstrap-backend-azure.sh
```
* **Comandos internos que ejecuta:**
  * `az group create --name sri-tfstate-rg --location eastus`: Crea el Resource Group de plataforma.
  * `az storage account create --name sritfstate23c5 --resource-group sri-tfstate-rg ...`: Crea la cuenta de almacenamiento encriptada con TLS 1.2. (El sufijo `23c5` garantiza unicidad global).
  * `az storage container create --name tfstate --account-name sritfstate23c5 --auth-mode key`: Crea el contenedor privado para almacenar `azure/terraform.tfstate`.
  * Pre-registra los Resource Providers necesarios (`Microsoft.ContainerService`, `Microsoft.Compute`, `Microsoft.Network`, `Microsoft.Storage`).

#### Paso 0.2: Registro Privado Azure Container Registry (ACR)
```bash
cd iac/azure/registry
terraform init
terraform apply -auto-approve
cd ../../..
```
* **Qué hace:** Despliega el recurso `azurerm_container_registry` con SKU Basic y nombre `sriacrtfm23c5`. Cuenta con `prevent_destroy = true` para proteger las imágenes compiladas por el pipeline de GitHub Actions.

#### Paso 0.3: Configurar Permisos RBAC de ACR
```bash
bash scripts/bootstrap-acr-rbac-azure.sh
```
* **Qué hace:**
  1. Asigna el rol `AcrPush` al Service Principal utilizado por GitHub Actions para que el pipeline publique imágenes sin contraseñas estáticas de administrador.
  2. Prepara la identidad gestionada para el rol `AcrPull` que usará el clúster AKS.

---

### 4.3 Fase 1: Aprovisionamiento de AKS con Terraform (Módulo Agnóstico)

El módulo agnóstico [iac/modules/kubernetes-cluster/azure/](file:///c:/Users/ASUS/Documents/Papi/Maestria%20DevOps%20UNIR/TFM/microservicio/sri-gitops-microservicio/iac/modules/kubernetes-cluster/azure) implementa la misma interfaz de variables que EKS para garantizar un código agnóstico y reutilizable.

#### Paso 1.1: Inicialización con Backend Remoto en Azure Storage
```bash
cd iac/azure
terraform init
```
* **Qué hace:** Conecta con el contenedor `tfstate` en `sritfstate23c5` y descarga el proveedor `hashicorp/azurerm` (~> 3.0).

#### Paso 1.2: Validación y Planificación
```bash
terraform validate
```
* **Salida esperada:** `Success! The configuration is valid.`

```bash
terraform plan -out=tfplan
```
* **Qué hace:** Calcula los recursos a crear en Azure:
  * Resource Group dedicado: `sri-aks-rg`.
  * Clúster gestionado: `sri-aks-cluster`.
  * Virtual Network y Subnet gestionada.
  * Default Node Pool: 3 nodos `Standard_B2s` o `Standard_D2s_v5`.
  * Kubelet Identity con permisos de red.

#### Paso 1.3: Aplicación de la Infraestructura en Azure
```bash
terraform apply tfplan
cd ../..
```
* **Qué hace:** Crea el clúster AKS en Azure (duración aproximada: 6 a 8 minutos).

---

### 4.4 Fase 2: Configuración del Clúster AKS y Addons

#### Paso 2.1: Descargar Credenciales del Clúster AKS
```bash
az aks get-credentials --resource-group sri-aks-rg --name sri-aks-cluster --overwrite-existing
```
* **Significado de flags:**
  * `--resource-group sri-aks-rg`: Resource Group donde reside el clúster.
  * `--name sri-aks-cluster`: Nombre del servicio AKS.
  * `--overwrite-existing`: Sobrescribe cualquier contexto previo en el archivo `~/.kube/config`.

Validar nodos activos:
```bash
kubectl get nodes
```
* **Salida esperada:** 3 nodos en estado `Ready`.

#### Paso 2.2: Vincular AKS con el Registro ACR (Permiso AcrPull)
```bash
az aks update --resource-group sri-aks-rg --name sri-aks-cluster --attach-acr sriacrtfm23c5
```
* **Significado de flags:**
  * `--attach-acr sriacrtfm23c5`: Asigna automáticamente el rol `AcrPull` de Entra ID a la identidad administrada del agente kubelet del clúster.
* **Qué hace:** Permite que los pods de Kubernetes descarguen las imágenes del backend y frontend de `sriacrtfm23c5.azurecr.io` sin necesidad de crear objetos `imagePullSecrets` manualmente.

#### Paso 2.3: Instalar ArgoCD en Azure AKS
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v2.11.0/manifests/install.yaml
kubectl wait --for=condition=Available deployment/argocd-server -n argocd --timeout=300s
```
* **Qué hace:** Despliega el plano de control GitOps en AKS.

---

### 4.5 Fase 3: Despliegue GitOps con ArgoCD (Overlay Azure)

```bash
# 1. Aplicar AppProject sri-facturacion en AKS
kubectl apply -f gitops/argocd/project.yaml

# 2. Desplegar la aplicación configurada para Azure
kubectl apply -f gitops/argocd/application-azure-aks.yaml
```
* **Qué hace:** ArgoCD procesa el overlay [gitops/overlays/azure-aks/](file:///c:/Users/ASUS/Documents/Papi/Maestria%20DevOps%20UNIR/TFM/microservicio/sri-gitops-microservicio/gitops/overlays/azure-aks):
  * Reemplaza las imágenes por las del registro ACR: `sriacrtfm23c5.azurecr.io/sri-backend:latest` y `sri-frontend:latest`.
  * Inyecta el ConfigMap con `CLOUD_PROVIDER: azure`.
  * Sincroniza los Deployments, Services y el HPA.

Comprobar sincronización:
```bash
kubectl get application sri-facturacion-azure-aks -n argocd
```
* **Salida esperada:** `Synced` y `Healthy`.

---

### 4.6 Fase 4: Despliegue del Stack de Observabilidad en AKS

```bash
kubectl apply -f gitops/argocd/application-monitor-azure.yaml
```
* **Qué hace:** Despliega el stack unificado de Prometheus y Grafana en el namespace `monitoring` de AKS, utilizando la StorageClass nativa de Azure (`managed-csi` / Azure Disk) para el almacenamiento de métricas.

---

### 4.7 Fase 5: Verificación de IP Pública, Tráfico y Telemetría

Obtener la IP pública asignada por el Azure Load Balancer:
```bash
kubectl get svc sri-frontend-svc -n sri-facturacion
```
* **Salida esperada:** La columna `EXTERNAL-IP` mostrará una dirección IP pública enrutada por Azure (ej. `20.120.45.18`).

Comprobar respuesta del endpoint multi-cloud en Azure:
```bash
curl -s http://<EXTERNAL-IP>:8088/api/v1/version
```
* **Salida esperada:**
```json
{
  "version": "1.0.0",
  "cloud": "azure",
  "cluster": "sri-aks-cluster",
  "hostname": "sri-backend-xxxxxxxxxx"
}
```

---

### 4.8 Fase 6: FinOps y Destrucción Limpia en Azure ($0/h)

Para apagar el entorno y eliminar cualquier costo de cómputo en Azure:

#### Paso 6.1: Eliminar Aplicaciones de ArgoCD y Balanceadores de Azure
```bash
# Eliminar las aplicaciones en cascada
kubectl delete application sri-monitor-azure-aks -n argocd --cascade=foreground
kubectl delete application sri-facturacion-azure-aks -n argocd --cascade=foreground

# Eliminar el servicio frontend para liberar la IP pública
kubectl delete svc sri-frontend-svc -n sri-facturacion --ignore-not-found=true
```

#### Paso 6.2: Destrucción de la Infraestructura con Terraform
```bash
cd iac/azure
terraform destroy -auto-approve
cd ../..
```
* **Qué hace:**
  1. Destruye el clúster AKS (`sri-aks-cluster`) y todos sus nodos.
  2. Destruye el Resource Group `sri-aks-rg`.
  3. Gracias al bloque `prevent_deletion_if_contains_resources = false` en `main.tf`, se purgan en cascada todas las reglas de métricas y recursos dinámicos de Azure sin requerir limpieza manual.
  4. La facturación en Azure vuelve a **$0.00/h**.
* **Recursos preservados:** El Resource Group de plataforma `sri-tfstate-rg`, el Storage Account con el estado y el Container Registry `sriacrtfm23c5`.

---

## 5. Guía Rápida de Troubleshooting y Mitigación de Errores

| Síntoma / Error | Entorno | Causa Raíz | Solución Inmediata |
| :--- | :--- | :--- | :--- |
| `namespace kube-system is not permitted in project` | Local / AWS / Azure | El AppProject de ArgoCD tiene destinos restringidos y el Helm chart monitorea componentes en `kube-system`. | Agregar `namespace: "*"` o `kube-system` a la lista `destinations` de `gitops/argocd/project.yaml` y aplicar con `kubectl apply -f`. |
| `HPA: unable to fetch metrics` (`<unknown>/80%`) | AWS / Azure | El clúster carece de `metrics-server` o el servicio de métricas no tiene certificados aceptados. | Aplicar `kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml`. |
| `ImagePullBackOff` en pods de backend | AWS EKS | El nodo worker no tiene rol IAM con `AmazonEC2ContainerRegistryReadOnly`. | Verificar la política del NodeGroup en `iac/aws/main.tf` o confirmar que la imagen existe con `aws ecr list-images --repository-name sri-facturacion-service`. |
| `ImagePullBackOff` en pods de backend | Azure AKS | El clúster AKS no tiene el permiso `AcrPull` en el registro ACR. | Ejecutar `az aks update --resource-group sri-aks-rg --name sri-aks-cluster --attach-acr sriacrtfm23c5`. |
| `CrashLoopBackOff` al arrancar el backend | Todos | Variables de conexión a la base de datos Supabase incorrectas o Secret no montado. | Ejecutar `kubectl logs -n sri-facturacion -l app=sri-backend` y verificar el contenido del Secret `sri-db-secret`. |
| `OutOfSync` continuo en el Deployment de backend | Todos | Conflicto entre las réplicas deseadas en Git y las réplicas escaladas en tiempo real por el HPA. | Añadir la sección `ignoreDifferences` para `/spec/replicas` en la definición de la `Application` de ArgoCD (ya configurado en los manifiestos del proyecto). |
| `Storage Account name already taken` | Azure | El nombre de las cuentas de almacenamiento en Azure debe ser único en todo el mundo. | Ajustar el sufijo en `scripts/bootstrap-backend-azure.sh` e `iac/azure/main.tf` utilizando los últimos caracteres del Subscription ID. |
| `ALB huérfano factura tras destroy` | AWS | Se ejecutó `terraform destroy` sin haber borrado el recurso `Ingress` de Kubernetes previamente. | Ejecutar `kubectl delete ingress sri-ingress -n sri-facturacion` antes de proceder al destroy de Terraform. |
