# 🎓 Guion de Defensa ante el Tribunal del TFM (5 Minutos)
## GitOps Multicloud: Observabilidad DORA y Arquitectura Desacoplada Flask / FastAPI
**Maestría en DevOps y Cloud Computing — UNIR**  
**Autores:** Darwin Augusto Calle Loja, Juan Carlos Cela Palacios, Luis Patricio Cuascota Tanicuchi  

---

## ⏱️ Estructura Temporal del Discurso (5 Minutos Exactos)

```
[00:00 - 01:00]  1. Introducción, Problemática del SRI y Objetivo del Bucle de Feedback
[01:00 - 02:15]  2. Arquitectura de Aplicación: Frontend Flask + Backend FastAPI + Supabase
[02:15 - 03:30]  3. Sistema de Observabilidad: Prometheus, Grafana y Métricas DORA
[03:30 - 04:30]  4. Resultados Cuantitativos: Línea Base SRI vs. Nivel Élite DORA
[04:30 - 05:00]  5. Conclusión de Cierre y Verificación de Hipótesis
```

---

## 🎤 Guion de Presentación Verbal

### Minuto 0:00 – 01:00 | 1. Introducción, Problemática y Objetivo 3
> *"Estimados miembros del tribunal, buenos días.*
>
> *El Servicio de Rentas Internas del Ecuador históricamente ha operado sobre arquitecturas monolíticas y servidores estáticos, enfrentando cuellos de botella severos: despliegues quincenales, resolución de incidentes de más de 4 horas y alta tasa de fallos manuales durante los picos de recaudación fiscal.*
>
> *Para resolver esta deuda técnica, nuestro Trabajo de Fin de Máster implementó una arquitectura GitOps Multicloud agnóstica entre AWS EKS y Azure AKS. Sin embargo, como lo exige la metodología científica Design Science Research (DSR), un artefacto de ingeniería debe evaluarse con rigor empírico.*
>
> *Aquí es donde entra nuestro **Objetivo Específico 3: el Bucle de Feedback y la Observabilidad**, diseñado para instrumentar la telemetría en tiempo real mediante Prometheus y Grafana, evaluar la autocuración del sistema ante desviaciones (Drift Detection) y medir cuantitativamente el impacto operativo a través de las 4 métricas DORA."*

---

### Minuto 01:00 – 02:15 | 2. Arquitectura de la Aplicación: Flask + FastAPI Desacoplados
> *"Para garantizar la portabilidad y la seguridad institucional sin comprometer el rendimiento, rediseñamos el servicio bajo una **arquitectura desacoplada en dos capas independientes**, cumpliendo estrictamente con el principio de que el frontend jamás accede directamente a la persistencia:*
>
> 1. **Backend de Alto Rendimiento (FastAPI - Python 3.12):**
>    *Expone una API REST asíncrona sobre Uvicorn (puerto 5000), encargada de la lógica tributaria del SRI. Incorpora autenticación mediante tokens JWT (`POST /api/v1/auth/login`), consulta y actualización de contribuyentes con validación sintáctica estricta de 13 dígitos para el RUC (`GET/PUT /api/v1/contribuyente/<ruc>`). Toda la persistencia reside en **Supabase (PostgreSQL)** con credenciales protegidas e inyectadas por variables de entorno y contraseñas hasheadas con `bcrypt` (cost 12).*
>
> 2. **Frontend Institucional y Seguro (Flask):**
>    *Opera en el puerto 8080 con renderizado del lado del servidor (SSR) y estilos limpios en Tailwind CSS. Gestiona la sesión del usuario mediante cookies seguras HTTP-only y un decorador `@login_required`. Consume la API del backend de forma 100% asíncrona mediante Fetch API, proporcionando estados de carga inmediatos con spinners, máscaras de entrada para evitar errores humanos y notificaciones flotantes (Toasts).*
>
> *Ambos componentes están contenerizados en Dockerfiles multi-stage independientes, enrutados por Ingress (`/api` al backend y `/` al frontend) y desacoplados del clúster mediante Kustomize."*

---

### Minuto 02:15 – 03:30 | 3. Sistema de Observabilidad: Prometheus, Grafana y Métricas DORA
> *"En el apartado de observabilidad, implementamos el stack nativo de nube **kube-prometheus-stack** orquestado por Prometheus Operator y sincronizado de forma declarativa mediante ArgoCD.*
>
> *La arquitectura de observabilidad cumple tres funciones cardinales:*
> 1. **Telemetría Inmutable Multicloud:** Prometheus recolecta métricas de infraestructura (CPU, memoria, réplicas, estado de pods) y métricas de sincronización de ArgoCD tanto en AWS como en Azure y en nuestro entorno local optimizado.
> 2. **Dashboard DORA en Grafana:** Exportamos e implementamos un tablero visual (`dashboard-dora.json`) que rastrea los 4 pilares fundamentales de rendimiento DevOps definidos por Google DORA.
> 3. **Validación de la Autocuración (Self-Healing):** Mediante la reconciliación continua de ArgoCD, el sistema detecta en segundos cualquier alteración manual en caliente de los pods y restaura automáticamente el estado declarado en Git, generando alertas y métricas inmediatas en el tablero de Grafana."*

---

### Minuto 03:30 – 04:30 | 4. Resultados Cuantitativos: Línea Base vs. Ecosistema GitOps
> *"Para validar experimentalmente la solución, ejecutamos 24 pruebas controladas durante un ciclo representativo de 4 semanas. Los resultados telemetrados frente a la línea base tradicional del SRI arrojaron cifras contundentes:*
>
> * Primero, **Deployment Frequency (Frecuencia de Despliegue):** Pasamos de despliegues quincenales a despliegues **bajo demanda y múltiples veces al día**, alcanzando nivel **Élite**.
> * Segundo, **Lead Time for Changes (Tiempo de Ciclo):** De más de 5 días hábiles (432.000 segundos) se redujo a una mediana de **255 segundos (~4,25 minutos)**. Esto representa una **mejora del 99,94%** en la velocidad de entrega de software.
> * Tercero, **Change Failure Rate (Tasa de Fallos):** Se redujo del 18% mensual en el SRI a **0%** en producción, gracias a que el pipeline CI/CD impone pruebas unitarias automatizadas con Pytest y escaneo de vulnerabilidades con Trivy previo al merge.
> * Y cuarto, **Mean Time to Recovery (MTTR):** Frente a caídas o desvíos de infraestructura que tomaban más de 4 horas de intervención manual, la autocuración de Kubernetes y ArgoCD restauró el servicio en una mediana de **13,5 segundos** (12 s en AWS y 15 s en Azure), lo que constituye una **reducción del 99,90% en el tiempo de inactividad**."*

---

### Minuto 04:30 – 05:00 | 5. Conclusión y Cierre
> *"En conclusión, señores miembros del tribunal:
> 
> Demostramos que la combinación de una arquitectura de microservicios desacoplada (Flask + FastAPI + Supabase), junto con el paradigma GitOps y un sistema de observabilidad integral en Prometheus y Grafana, no solo garantiza la portabilidad real multicloud con un 0% de alteración de código aplicativa ($P_{\Delta code} = 0\%$), sino que posiciona la gestión tecnológica del SRI en el percentil **Élite** de la industria global.
> 
> Quedamos a su entera disposición para cualquier pregunta. Muchas gracias."*

---

## 📊 Matriz Comparativa de Respaldo Técnico (Para Preguntas del Tribunal)

| Métrica DORA | Línea Base (SRI Tradicional) | Solución GitOps Multicloud | Impacto / % Mejora | Nivel DORA |
| :--- | :--- | :--- | :--- | :---: |
| **Deployment Frequency (DF)** | Menor a 1 vez por semana (quincenal) | Bajo demanda (múltiples al día) | Despliegue continuo automatizado | **Élite** |
| **Lead Time for Changes (LTC)** | > 5 días hábiles ($432.000\text{ s}$) | Mediana global: **$255\text{ s}$ ($4,25\text{ min}$)** | **$99,94\%$ de reducción** | **Élite** |
| **Change Failure Rate (CFR)** | $\approx 18\%$ mensual | **$0\%$** (en las 24 ejecuciones) | Errores mitigados en CI (Pytest/Trivy) | **Élite** |
| **Mean Time to Recovery (MTTR)**| > 4 horas ($14.400\text{ s}$) | Mediana global: **$13,5\text{ s}$** ($12\text{ s}$ AWS / $15\text{ s}$ Azure) | **$99,90\%$ de reducción** | **Élite** |

---

## 🛡️ Preguntas Frecuentes del Tribunal y Respuestas Sugeridas

### P1: ¿Por qué decidieron separar el Frontend en Flask y el Backend en FastAPI en lugar de un monolito?
> **Respuesta:** *"Por tres razones clave: (1) **Separación de responsabilidades y seguridad**: el Frontend jamás debe tener credenciales directas a la base de datos Supabase ni acceso a la red de datos; solo consume la API mediante JWT. (2) **Rendimiento asíncrono**: FastAPI y Uvicorn proporcionan alto rendimiento asíncrono y serialización con Pydantic para el procesamiento fiscal en el backend, mientras Flask con Tailwind CSS gestiona el renderizado de vistas seguras (SSR) y sesiones HTTP-only. (3) **Escalabilidad independiente**: el HPA escala los pods del backend ante carga fiscal de consultas sin necesidad de sobredimensionar la capa de presentación."*

### P2: ¿Cómo mide exactamente el sistema las métricas DORA en la observabilidad?
> **Respuesta:** *"Utilizamos dos fuentes de verdad automatizadas: el tiempo de integración continua ($T_{CI}$) se extrae de GitHub Actions API midiendo desde `check_run.started_at` hasta la finalización de pruebas y build. El tiempo de despliegue ($T_{Sync}$) lo captura Prometheus a través de los eventos de ArgoCD al pasar de estado `OutOfSync` a `Synced` y `Healthy`. Grafana agrega estas series temporales mediante el dashboard DORA, utilizando la mediana (percentil 50) para eliminar distorsiones por arranques en frío (cold starts)."*

### P3: ¿Cómo se maneja la observabilidad en entornos locales sin saturar los recursos de hardware?
> **Respuesta:** *"En el repositorio implementamos `gitops/monitoring/values-local.yaml`, donde adaptamos el chart Helm de Prometheus Operator restringiendo el almacenamiento a un volumen ligero de 2Gi, ajustando los intervalos de retención de telemetría y exponiendo Grafana por NodePort 30300. Esto permite validar todo el stack de observabilidad y métricas DORA en local sin requerir suscripciones costosas ni saturar el disco de desarrollo."*
