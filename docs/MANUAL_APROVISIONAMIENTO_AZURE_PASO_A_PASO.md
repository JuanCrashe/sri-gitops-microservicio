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
[FASE 1: PREPARACIÓN LOCAL & AZURE CLI (az login)] ⏳ EN CURSO
                        │
                        ▼
[FASE 2: RECURSOS BASE STORAGE SA / ACR]           ⏳ PENDIENTE
                        │
                        ▼
[FASE 3: TERRAFORM APPLY (CLÚSTER AKS)]            ⏳ PENDIENTE
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

*(Fases 3 a 8 se actualizarán conforme ejecutemos el aprovisionamiento).*

