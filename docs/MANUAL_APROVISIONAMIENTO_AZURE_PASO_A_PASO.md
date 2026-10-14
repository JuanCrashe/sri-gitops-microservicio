# 🚀 Manual Detallado Paso a Paso: Aprovisionamiento y Despliegue en Azure (Azure Kubernetes Service - AKS)
## Trabajo de Fin de Máster (TFM) — UNIR
**Proyecto:** Microservicio SRI Facturación — GitOps Multicloud  
**Autores:** Darwin Augusto Calle Loja, Juan Carlos Cela Palacios, Luis Patricio Cuascota Tanicuchi  
**Suscripción:** Azure for Students ($100 USD Crédito)

---

## 📌 Introducción y Propósito del Documento
Este documento guía paso a paso el aprovisionamiento de la arquitectura en **Microsoft Azure** utilizando **Azure Kubernetes Service (AKS)**, Infraestructura como Código (IaC) con **Terraform**, y entrega continua declarativa con **ArgoCD (GitOps)**.

Está diseñado específicamente para:
1. Adaptar el despliegue a las restricciones y cuotas de **Azure for Students** (evitando bloqueos por cuota de vCPUs).
2. Configurar la plataforma base de almacenamiento de estado (Azure Blob Storage) y registro privado de imágenes (**Azure Container Registry - ACR**).
3. Aprovisionar el clúster AKS gestionado con 2 nodos optimizados y desplegar el microservicio desacoplado.
4. Desplegar observabilidad con Prometheus Operator y Grafana DORA.
5. Garantizar un protocolo estricto de **FinOps Teardown** al finalizar para retornar el consumo a **$0.00/h**.

---

## 🗺️ Mapa de Fases del Aprovisionamiento en Azure

```
[FASE 1: PREPARACIÓN LOCAL & AZURE CLI (az login)] ✅ COMPLETADA
                        │
                        ▼
[FASE 2: RECURSOS BASE STORAGE SA / ACR]           ✅ COMPLETADA
                        │
                        ▼
[FASE 3: TERRAFORM APPLY (CLÚSTER AKS 2 NODOS)]    ⏳ EN CURSO
                        │
                        ▼
[FASE 4: KUBECTL & CONTROLLERS (ARGOCD/METRICS)]   ⏳ PENDIENTE
                        │
                        ▼
[FASE 5: COMPILACIÓN & PUSH DE IMÁGENES A ACR]     ⏳ PENDIENTE
                        │
                        ▼
[FASE 6: GITOPS ARGOCD & APLICACIÓN EN VIVO]       ⏳ PENDIENTE
                        │
                        ▼
[FASE 7: OBSERVABILIDAD PROMETHEUS & GRAFANA DORA] ⏳ PENDIENTE
                        │
                        ▼
[FASE 8: FINOPS TEARDOWN LIMPIO ($0.00/h)]         ⏳ PENDIENTE
```

---

## 🛠️ Consideraciones Clave para "Azure for Students" (FinOps & Cuotas)

> [!IMPORTANT]
> **Límite de Cuota Regional de vCPUs:**  
> Las cuentas de *Azure for Students* vienen con cuotas estrictas por región (normalmente un máximo de **4 vCPUs** en familias Standard Dsv3 o B-series).
> * **Configuración en AWS previa:** 3 nodos `t3.medium` (6 vCPUs).
> * **Configuración adaptada a Azure for Students:** 
>   * Opción A: **2 nodos `Standard_D2s_v3`** (2 x 2 = 4 vCPUs exactos, 16 GB RAM totales).
>   * Opción B: **2 nodos `Standard_B2s`** (2 x 2 = 4 vCPUs exactos, 8 GB RAM totales).
>   * Región recomendada: **`eastus`** (mayor disponibilidad de recursos y menor latencia).

> [!NOTE]
> **Nombres Globalmente Únicos:**  
> En Azure, tanto el **Storage Account** del estado de Terraform como el **Azure Container Registry (ACR)** deben tener un nombre único en todo el mundo (solo letras minúsculas y números, entre 3 y 24 caracteres). Se utilizará un sufijo personalizado derivado del Subscription ID.

---

## 🛠️ Fase 1: Preparación del Entorno Local y Autenticación con Azure

### 1.1 Instalación de Azure CLI en Windows
En una ventana de **PowerShell**:
```powershell
winget install -e --id Microsoft.AzureCLI
```
*(Tras finalizar la instalación, reinicia la terminal o abre una nueva pestaña para que reconozca el comando `az`).*

### 1.2 Inicio de Sesión Interactivo en Azure
```powershell
az login
```
* Se abrirá automáticamente el navegador predeterminado.
* Inicia sesión con tus credenciales institucionales de **Azure for Students**.

### 1.3 Verificación de Suscripción Activa
```powershell
az account show --output table
```
* **Suscripción confirmada:** `Azure for Students`
* **Subscription ID:** `7cf3c7d8-37da-45a5-87c4-209a2f571acd`
* **Sufijo único asignado:** `1acd`

---

## 🪣 Fase 2: Plataforma Base de Larga Vida (Storage Account y ACR)

En Azure, el estado de Terraform (`.tfstate`) se almacena en un contenedor de Azure Blob Storage dentro de un **Storage Account**, y las imágenes Docker en **Azure Container Registry (ACR)**.

### 2.1 Definición de Variables de Plataforma
```powershell
$RG="sri-tfstate-rg"
$LOCATION="canadacentral"
$STORAGE="sritfstate1acd"
$CONTAINER="tfstate"
$ACR="sriacrtfm1acd"
```

### 2.2 Creación del Resource Group y Storage Account
```powershell
# 1. Crear el Resource Group contenedor del estado
az group create --name $RG --location $LOCATION

# 2. Crear el Storage Account con cifrado Blob y TLS 1.2
az storage account create `
  --name $STORAGE `
  --resource-group $RG `
  --location $LOCATION `
  --sku Standard_LRS `
  --encryption-services blob `
  --min-tls-version TLS1_2

# 3. Crear el contenedor Blob para el archivo de estado
az storage container create `
  --name $CONTAINER `
  --account-name $STORAGE `
  --auth-mode key
```

### 2.3 Registro de Resource Providers Necesarios para AKS
Para que Azure permita crear clústeres Kubernetes, instancias virtuales y redes, registramos los proveedores oficiales:
```powershell
az provider register --namespace Microsoft.ContainerService
az provider register --namespace Microsoft.Compute
az provider register --namespace Microsoft.Network
az provider register --namespace Microsoft.Storage
az provider register --namespace Microsoft.KeyVault
az provider register --namespace Microsoft.ContainerRegistry
```

### 2.4 Creación del Azure Container Registry (ACR)
```powershell
az acr create `
  --resource-group $RG `
  --name $ACR `
  --sku Basic `
  --admin-enabled true `
  --location $LOCATION
```

---

## 🏗️ Fase 3: Aprovisionamiento del Clúster Azure AKS (Terraform)

El código de Terraform en `iac/azure` provisiona:
* **Resource Group:** `sri-aks-rg` en `canadacentral`.
* **Clúster AKS:** `sri-aks-cluster` ejecutando Kubernetes `v1.36` (versión oficial por defecto en canadacentral).
* **Node Pool:** 2 nodos `Standard_D2s_v3` (4 vCPUs y 16 GB RAM totales, adaptado al límite de estudiante).
* **Identidad:** Identidad Administrada del Sistema (`SystemAssigned`).

### 3.1 Cargar Terraform en el PATH (si es necesario)
```powershell
$env:PATH += ";C:\Users\ASUS\AppData\Local\Microsoft\WinGet\Packages\Hashicorp.Terraform_Microsoft.Winget.Source_8wekyb3d8bbwe"
```

### 3.2 Inicializar el Directorio de Terraform
```powershell
cd "c:\Users\ASUS\Documents\Papi\Maestria DevOps UNIR\TFM\microservicio\sri-gitops-microservicio\iac\azure"
terraform init
```
* **Qué hace:** Conecta con el contenedor `tfstate` en `sritfstate1acd` y descarga el proveedor oficial `hashicorp/azurerm` (~> 3.0).

### 3.3 Validar el Plan de Ejecución
```powershell
terraform plan
```
* **Salida esperada:** `Plan: 2 to add, 0 to change, 0 to destroy.`
  1. `azurerm_resource_group.main` (`sri-aks-rg`)
  2. `azurerm_kubernetes_cluster.main` (`sri-aks-cluster`)

### 3.4 Desplegar la Infraestructura en Azure
```powershell
terraform apply -auto-approve
```
* **Tiempo estimado:** ~4 a 6 minutos.

### 3.5 Vincular el Registro ACR con AKS (Permiso de Pull Automático)
Una vez creado el clúster, vinculamos el ACR para que el kubelet descargue las imágenes sin necesitar secretos:
```powershell
az aks update --resource-group sri-aks-rg --name sri-aks-cluster --attach-acr sriacrtfm1acd
```

### 3.6 Descargar Credenciales de Kubectl
```powershell
az aks get-credentials --resource-group sri-aks-rg --name sri-aks-cluster --overwrite-existing
kubectl get nodes -o wide
```
* **Salida esperada:** 2 nodos en estado `Ready`.

---

## 🐙 Fase 4: Despliegue de ArgoCD en Azure AKS

Para la gestión declarativa de las aplicaciones bajo el enfoque GitOps, instalamos el operador oficial de ArgoCD en su propio espacio de nombres.

### 4.1 Crear Namespace e Instalar Manifiestos de ArgoCD
```powershell
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v2.11.0/manifests/install.yaml
```

### 4.2 Esperar a que los Pods de ArgoCD estén Listos
```powershell
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s
```

### 4.3 Registrar el AppProject de la Aplicación
```powershell
kubectl apply -f "c:\Users\ASUS\Documents\Papi\Maestria DevOps UNIR\TFM\microservicio\sri-gitops-microservicio\gitops\argocd\project.yaml"
```

### 4.4 Obtener la Contraseña Inicial del Administrador de ArgoCD
```powershell
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String((kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}")))
```
* **Usuario:** `admin`

---

## 📦 Fase 5: Publicación de Imágenes Docker en Azure Container Registry (ACR)

Las imágenes construidas localmente se etiquetan con el dominio de Azure Container Registry (`sriacrtfm1acd.azurecr.io`) y se envían mediante Docker.

### 5.1 Iniciar Sesión en el ACR
```powershell
az acr login --name sriacrtfm1acd
```
* **Salida esperada:** `Login Succeeded`

### 5.2 Etiquetar las Imágenes Locales para ACR
```powershell
docker tag sri-backend:latest sriacrtfm1acd.azurecr.io/sri-backend:latest
docker tag sri-frontend:latest sriacrtfm1acd.azurecr.io/sri-frontend:latest
```

### 5.3 Subir las Imágenes al Registro Privado de Azure
```powershell
docker push sriacrtfm1acd.azurecr.io/sri-backend:latest
docker push sriacrtfm1acd.azurecr.io/sri-frontend:latest
```

### 5.4 Verificar las Imágenes en Azure
```powershell
az acr repository list --name sriacrtfm1acd --output table
```
* **Salida esperada:**
  - `sri-backend`
  - `sri-frontend`

---

## 🚀 Fase 6: Secretos y Despliegue de la Aplicación SRI con GitOps

### 6.1 Crear el Namespace de la Aplicación
```powershell
kubectl create namespace sri-facturacion
```

### 6.2 Crear el Secreto de Kubernetes para Producción
Creamos el secreto nativo de Kubernetes que inyecta la conexión a Supabase y claves criptográficas:
```powershell
kubectl create secret generic sri-facturacion-secrets `
  --namespace sri-facturacion `
  --from-literal=SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVxbXVsa25laXpieWtzcXVxc3JnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODMyMTEyNTYsImV4cCI6MjA5ODc4NzI1Nn0.AqDdDrj4Q566Vqn68fLAIrkWBRTvHVBA9tkj_FI661E" `
  --from-literal=JWT_SECRET="super-secret-key-cambiar-en-produccion" `
  --from-literal=FLASK_SECRET_KEY="clave_secreta_frontend_aqui"
```

### 6.3 Desplegar la Aplicación SRI vía ArgoCD
```powershell
kubectl apply -f "c:\Users\ASUS\Documents\Papi\Maestria DevOps UNIR\TFM\microservicio\sri-gitops-microservicio\gitops\argocd\application-azure-aks.yaml"
```

### 6.4 Monitorear el Despliegue de Pods
```powershell
kubectl get pods -n sri-facturacion -o wide
```
* **Salida esperada:** 3 réplicas de `sri-backend` y 3 réplicas de `sri-frontend` en estado `Running`.

---

## 🌐 Fase 7: Validación del Frontend y Consumo del SRI

### 7.1 Obtener la IP Pública del Frontend (LoadBalancer de Azure)
```powershell
kubectl get svc sri-frontend-svc -n sri-facturacion -w
```
* Una vez que la columna `EXTERNAL-IP` pase de `<pending>` a una IP pública (ej. `20.x.x.x`), presiona `Ctrl + C`.

### 7.2 Probar la Aplicación en el Navegador Web
* Abre tu navegador e ingresa a: `http://<EXTERNAL-IP>`
* Inicia sesión con las credenciales de prueba configuradas en Supabase.
* Consulta un RUC (ej. `1790016919001`) y valida la actualización de datos asíncrona.

---

## 📊 Fase 8: Despliegue del Stack de Observabilidad (Prometheus + Grafana + Métricas DORA)

Desplegamos el stack unificado de observabilidad gestionado por GitOps con ArgoCD en el namespace `monitoring`.

### 8.1 Crear el Namespace y Registrar el Dashboard DORA
```powershell
kubectl create namespace monitoring

kubectl create configmap grafana-dashboard-dora -n monitoring `
  --from-file="dashboard-dora.json=c:\Users\ASUS\Documents\Papi\Maestria DevOps UNIR\TFM\microservicio\sri-gitops-microservicio\gitops\monitoring\dashboard-dora.json"

kubectl label configmap grafana-dashboard-dora -n monitoring grafana_dashboard=1
```

### 8.2 Desplegar la Aplicación de Monitoreo con ArgoCD
```powershell
kubectl apply -f "c:\Users\ASUS\Documents\Papi\Maestria DevOps UNIR\TFM\microservicio\sri-gitops-microservicio\gitops\argocd\application-monitor-azure.yaml"
```

### 8.3 Monitorear el Despliegue de los Pods de Observabilidad
```powershell
kubectl get pods -n monitoring -w
```
* **Pods desplegados:**
  - `sri-monitoring-kube-p-operator-*` (Prometheus Operator)
  - `prometheus-sri-monitoring-kube-p-prometheus-0` (Servidor Prometheus)
  - `sri-monitoring-grafana-*` (Servidor Grafana)
  - `sri-monitoring-kube-state-metrics-*` (Métricas de K8s)
  - `sri-monitoring-prometheus-node-exporter-*` (DaemonSet en cada nodo)

### 8.4 Acceder a la Interfaz de Grafana
```powershell
kubectl port-forward svc/sri-monitoring-grafana -n monitoring 3000:80
```
* **URL:** [http://localhost:3000](http://localhost:3000)
* **Usuario:** `admin`
* **Contraseña:** `prom-operator`
* **Dashboard incluido:** *SRI GitOps - Métricas DORA y Resiliencia Multicloud* (UID: `sri-dora-metrics`).

---

## 💰 Fase 9: FinOps - Desmantelamiento y Limpieza Preventiva de Costos

> [!WARNING]
> La cuenta de estudiante de Azure dispone de un crédito limitado ($100 USD). Para no agotar dicho crédito, al finalizar la prueba o demostración se deben eliminar los recursos que consumen cómputo por hora.

### 9.1 Eliminar Aplicaciones de ArgoCD y Balanceadores
```powershell
kubectl delete application sri-monitor-azure-aks -n argocd --cascade=foreground
kubectl delete application sri-facturacion-azure-aks -n argocd --cascade=foreground
kubectl delete svc sri-frontend-svc -n sri-facturacion --ignore-not-found=true
```

### 9.2 Destruir la Infraestructura de AKS (Terraform)
```powershell
cd "c:\Users\ASUS\Documents\Papi\Maestria DevOps UNIR\TFM\microservicio\sri-gitops-microservicio\iac\azure"
terraform destroy -auto-approve
```
* **Qué destruye:** El clúster `sri-aks-cluster`, los 2 nodos `Standard_D2s_v3`, el LoadBalancer público y el Resource Group `sri-aks-rg`.
* **Tiempo estimado:** ~4 a 6 minutos.

### 9.3 Eliminar los Recursos Base (Opcional - solo si se desea eliminar todo)
Si deseas eliminar también el registro ACR y el estado de Terraform:
```powershell
az group delete --name sri-tfstate-rg --yes --no-wait
```



