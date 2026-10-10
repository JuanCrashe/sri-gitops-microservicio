# 🔌 Guía Operativa: Apagado Limpio (Teardown) y Reanudación del Entorno Local

**Proyecto:** GitOps Multicloud: Implementación de Pipelines CI/CD con Infraestructura como Código Agnóstica para la Portabilidad de Microservicios  
**Máster:** MUDEVOPS — UNIR  
**Propósito:** Manual para desmontar completamente el entorno local liberando memoria RAM, CPU y disco, y volver a levantarlo en minutos cualquier otro día para demostraciones o evaluaciones.

---

## 📑 Tabla de Contenidos

1. [Conceptos Clave del Ciclo de Vida Local](#1-conceptos-clave-del-ciclo-de-vida-local)
2. [Parte 1: Apagado Limpio y Cancelación de Recursos (Teardown)](#parte-1-apagado-limpio-y-cancelación-de-recursos-teardown)
   - [Paso 1.1: Eliminar las Aplicaciones en ArgoCD](#paso-11-eliminar-las-aplicaciones-en-argocd)
   - [Paso 1.2: Eliminar los Namespaces de Trabajo](#paso-12-eliminar-los-namespaces-de-trabajo)
   - [Paso 1.3: Eliminar ArgoCD (Opcional)](#paso-13-eliminar-argocd-opcional)
   - [Paso 1.4: Liberar Almacenamiento y Recursos Residuales](#paso-14-liberar-almacenamiento-y-recursos-residuales)
   - [Paso 1.5: Verificación de Clúster Vacío](#paso-15-verificación-de-clúster-vacío)
3. [Parte 2: Reanudación y Levantamiento en una Nueva Sesión](#parte-2-reanudación-y-levantamiento-en-una-nueva-sesión)
   - [Paso 2.1: Preflight del Clúster Kubernetes](#paso-21-preflight-del-clúster-kubernetes)
   - [Paso 2.2: Verificar o Reinstalar ArgoCD](#paso-22-verificar-o-reinstalar-argocd)
   - [Paso 2.3: Inyectar Secretos de Base de Datos Supabase](#paso-23-inyectar-secretos-de-base-de-datos-supabase)
   - [Paso 2.4: Desplegar el Microservicio y Observabilidad con GitOps](#paso-24-desplegar-el-microservicio-y-observabilidad-con-gitops)
   - [Paso 2.5: Verificación de Salud y Portales Web](#paso-25-verificación-de-salud-y-portales-web)
4. [Resumen Rápido (Cheat Sheet)](#4-resumen-rápido-cheat-sheet)

---

## 1. Conceptos Clave del Ciclo de Vida Local

En un entorno local basado en **Docker Desktop** con Kubernetes:
* **Persistencia entre reinicios:** Si apagas tu PC o cierras Docker Desktop sin borrar nada, Kubernetes intentará restaurar los pods al volver a encenderlo. Sin embargo, esto puede saturar memoria al iniciar el sistema o dejar componentes en estados inconsistentes si la máquina hiberna.
* **Buenas Prácticas de Ingeniería (Clean Teardown):** La mejor práctica para sesiones de laboratorio y defensas de TFM es **desmontar los recursos declarativamente** al terminar. Esto garantiza que la próxima vez que levantes el entorno, validarás desde cero la capacidad de aprovisionamiento automatizado e idempotente de tu arquitectura.

---

## Parte 1: Apagado Limpio y Cancelación de Recursos (Teardown)

Sigue estos pasos en tu terminal (PowerShell o bash) cuando termines tu jornada de trabajo:

### Paso 1.1: Eliminar las Aplicaciones en ArgoCD
El primer paso es indicarle a ArgoCD que elimine las aplicaciones. Al tener configurado el finalizador `resources-finalizer.argocd.argoproj.io`, ArgoCD borrará en cascada todos los pods, servicios, deployments y volúmenes asociados:

```bash
kubectl delete application sri-monitor-local -n argocd
kubectl delete application sri-facturacion-local -n argocd
```
* **Qué hace:** 
  * Borra los 5 pods del microservicio (`sri-backend` y `sri-frontend`), los servicios LoadBalancer y el HPA.
  * Borra los pods de Prometheus, Grafana, Node-Exporter y Kube-State-Metrics.

---

### Paso 1.2: Eliminar los Namespaces de Trabajo
Para garantizar que no queden secretos residuales, ConfigMaps ni Claims de almacenamiento (PVC):

```bash
kubectl delete namespace sri-facturacion
kubectl delete namespace monitoring
```
* **Qué hace:** Destruye los espacios de nombres completos y purga el volumen persistente de 2Gi del disco local de Docker Desktop.
* **Tiempo de espera:** Suele tardar entre 10 y 20 segundos mientras Kubernetes termina de drenar los recursos.

---

### Paso 1.3: Eliminar ArgoCD (Opcional según tu preferencia)
Tienes dos alternativas con ArgoCD:
* **Opción Recomendada (Dejar ArgoCD instalado):** Ocupa muy poca memoria en reposo y te ahorra 2 minutos la próxima vez. En este caso, **no ejecutes** el siguiente comando.
* **Opción Limpieza Total (Clúster 100% virgen):** Si quieres borrar todo vestigio de ArgoCD:
  ```bash
  kubectl delete namespace argocd
  ```

---

### Paso 1.4: Liberar Almacenamiento y Recursos Residuales
Si durante tus pruebas compilaste varias imágenes intermedias de Docker (`v1.1.0`, `v1.2.0`, etc.) y deseas recuperar espacio en tu disco duro:

```bash
docker system prune -f
```
* **Qué hace:** Elimina contenedores detenidos, redes no utilizadas e imágenes sin etiquetar (*dangling images*) sin borrar las imágenes base de tu sistema.

---

### Paso 1.5: Verificación de Clúster Vacío
Comprueba que tu clúster ya no tiene cargas de trabajo activas:

```bash
kubectl get pods -A
```
* **Salida esperada:** Solo verás los pods esenciales del sistema en el namespace `kube-system` (como CoreDNS, kube-proxy, etcd) y `local-path-storage`.

¡Listo! En este punto los puertos `8088`, `5000`, `3000` y `443` quedan completamente liberados y puedes apagar o reiniciar tu computadora con tranquilidad.

---

## Parte 2: Reanudación y Levantamiento en una Nueva Sesión

Cuando vuelvas otro día y quieras levantar todo el entorno local rápidamente para hacer pruebas o una demostración, sigue este flujo:

### Paso 2.1: Preflight del Clúster Kubernetes
1. Abre **Docker Desktop** y asegúrate de que el icono en la barra inferior muestre *"Engine running"* y *"Kubernetes running"* (icono verde).
2. Verifica en tu terminal que el clúster responda:
   ```bash
   kubectl cluster-info
   ```

---

### Paso 2.2: Verificar o Reinstalar ArgoCD
Si mantuviste ArgoCD, verifica que sus pods estén activos:
```bash
kubectl get pods -n argocd
```

*(Si borraste el namespace `argocd` en la sesión anterior, reinstálalo en 2 comandos):*
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v2.11.0/manifests/install.yaml
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'
```

---

### Paso 2.3: Inyectar Secretos de Base de Datos Supabase
Crea el namespace de la aplicación y el secreto necesario para la conexión a la base de datos:

```bash
kubectl create namespace sri-facturacion --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic sri-db-secret -n sri-facturacion \
  --from-literal=DB_HOST="aws-0-us-east-1.pooler.supabase.com" \
  --from-literal=DB_PORT="6543" \
  --from-literal=DB_NAME="postgres" \
  --from-literal=DB_USER="postgres.jtuqawnhrvtquhyjkluh" \
  --from-literal=DB_PASSWORD="TU_PASSWORD_AQUI" \
  --from-literal=JWT_SECRET_KEY="sri_devops_secret_key_2026_super_segura" \
  --dry-run=client -o yaml | kubectl apply -f -
```

---

### Paso 2.4: Desplegar el Microservicio y Observabilidad con GitOps
Aplica los tres manifiestos declarativos del proyecto:

```bash
# 1. Permisos del proyecto en ArgoCD
kubectl apply -f gitops/argocd/project.yaml

# 2. Despliegue de la aplicación (Backend + Frontend + HPA)
kubectl apply -f gitops/argocd/application-local.yaml

# 3. Despliegue del Stack de Observabilidad (Prometheus + Grafana con PVC 2Gi)
kubectl apply -f gitops/argocd/application-monitor-local.yaml
```

ArgoCD tomará el control automáticamente, clonará el repositorio en su última versión de Git y levantará todas las cargas de trabajo.

Monitorea el arranque de los pods:
```bash
kubectl get pods -n sri-facturacion
kubectl get pods -n monitoring
```
*En aproximadamente 40 a 60 segundos todos los pods pasarán al estado `Running`.*

---

### Paso 2.5: Verificación de Salud y Portales Web
Una vez que los pods estén arriba, todos los accesos estarán nuevamente operativos:

* **Frontend Web SRI:** [http://localhost:8088](http://localhost:8088) (Credenciales: `1790011674001` / `1234` o `admin@sri.gob.ec` / `Admin2026*`).
* **Backend API REST:** [http://localhost:5000/api/v1/version](http://localhost:5000/api/v1/version)
* **Grafana Observabilidad:** [http://localhost:3000](http://localhost:3000) (`admin` / `prom-operator`).
* **Consola ArgoCD:** [https://localhost](https://localhost) (`admin`).

---

## 4. Resumen Rápido (Cheat Sheet)

### Para Apagar y Cancelar Todo Hoy:
```bash
kubectl delete application sri-monitor-local -n argocd
kubectl delete application sri-facturacion-local -n argocd
kubectl delete namespace sri-facturacion monitoring
```

### Para Volver a Levantar Todo Otro Día:
```bash
kubectl create namespace sri-facturacion
kubectl create secret generic sri-db-secret -n sri-facturacion --from-literal=DB_HOST="aws-0-us-east-1.pooler.supabase.com" --from-literal=DB_PORT="6543" --from-literal=DB_NAME="postgres" --from-literal=DB_USER="postgres.jtuqawnhrvtquhyjkluh" --from-literal=DB_PASSWORD="TU_PASSWORD_AQUI" --from-literal=JWT_SECRET_KEY="sri_devops_secret_key_2026_super_segura"
kubectl apply -f gitops/argocd/project.yaml
kubectl apply -f gitops/argocd/application-local.yaml
kubectl apply -f gitops/argocd/application-monitor-local.yaml
```
