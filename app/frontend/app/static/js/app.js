document.addEventListener('DOMContentLoaded', () => {
    
    // Toast Notification System
    const showToast = (message, type = 'success') => {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        const bgColor = type === 'success' ? 'bg-green-500' : 'bg-red-500';
        
        toast.className = `flex items-center w-full max-w-xs p-4 text-white ${bgColor} rounded-lg shadow toast-enter mb-2`;
        toast.innerHTML = `
            <div class="ml-3 text-sm font-normal">${message}</div>
            <button type="button" class="ml-auto -mx-1.5 -my-1.5 text-white hover:text-gray-200 rounded-lg p-1.5 inline-flex h-8 w-8" onclick="this.parentElement.remove()">
                <span class="sr-only">Close</span>
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path></svg>
            </button>
        `;
        
        container.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.classList.add('toast-leave');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    };

    // Helper para headers
    const getHeaders = () => {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${window.API_TOKEN}`
        };
    };

    // Lógica para Dashboard (Búsqueda)
    const searchForm = document.getElementById('search-form');
    const rucInput = document.getElementById('ruc-input');
    const searchBtn = document.getElementById('search-btn');
    const rucError = document.getElementById('ruc-error');
    
    if (searchForm && rucInput && searchBtn) {
        
        // Validación de 13 dígitos
        rucInput.addEventListener('input', (e) => {
            const val = e.target.value;
            if (val.length === 13 && /^\d+$/.test(val)) {
                searchBtn.disabled = false;
                rucError.classList.add('hidden');
            } else {
                searchBtn.disabled = true;
                if(val.length > 0) rucError.classList.remove('hidden');
            }
        });

        searchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const ruc = rucInput.value;
            if (ruc.length !== 13) return;

            // UI Loading state
            searchBtn.disabled = true;
            document.getElementById('search-text').classList.add('hidden');
            document.getElementById('search-spinner').classList.remove('hidden');

            try {
                // Hacer la consulta GET en backend para ver si existe
                const res = await fetch(`${window.BACKEND_URL}/api/v1/contribuyente/${ruc}`, {
                    headers: getHeaders()
                });
                
                if (res.ok) {
                    // Si existe, redirigir a detalle
                    window.location.href = `/contribuyente/${ruc}`;
                } else {
                    const errorData = await res.json();
                    showToast(errorData.error || 'El RUC ingresado no se encuentra registrado.', 'error');
                }
            } catch (err) {
                console.error(err);
                showToast('Error de conexión con el servidor', 'error');
            } finally {
                searchBtn.disabled = false;
                document.getElementById('search-text').classList.remove('hidden');
                document.getElementById('search-spinner').classList.add('hidden');
            }
        });
    }

    // Lógica para Detalle (Carga y Actualización)
    if (window.CURRENT_RUC) {
        const loadContribuyenteData = async () => {
            try {
                const res = await fetch(`${window.BACKEND_URL}/api/v1/contribuyente/${window.CURRENT_RUC}`, {
                    headers: getHeaders()
                });
                if (res.ok) {
                    const data = await res.json();
                    
                    // Fill form
                    document.getElementById('razon_social').value = data.razon_social || '';
                    document.getElementById('estado_ruc').value = data.estado_ruc || '';
                    document.getElementById('tipo_contribuyente').value = data.tipo_contribuyente || '';
                    document.getElementById('regimen_impositivo').value = data.regimen_impositivo || '';
                    document.getElementById('actividad_economica').value = data.actividad_economica || '';
                    
                    if (data.ultima_actualizacion) {
                        const date = new Date(data.ultima_actualizacion);
                        document.getElementById('ultima_actualizacion').textContent = date.toLocaleString();
                    }

                    // Badge color depending on state
                    const badge = document.getElementById('badge-estado');
                    badge.textContent = data.estado_ruc;
                    if(data.estado_ruc === 'ACTIVO') {
                        badge.className = 'px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800';
                    } else if(data.estado_ruc === 'SUSPENDIDO') {
                        badge.className = 'px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800';
                    } else {
                        badge.className = 'px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800';
                    }

                    // Show content
                    document.getElementById('initial-loader').classList.add('hidden');
                    document.getElementById('contribuyente-data').classList.remove('hidden');
                } else {
                    showToast('Error al cargar datos', 'error');
                    setTimeout(() => window.location.href = '/dashboard', 2000);
                }
            } catch (err) {
                console.error(err);
                showToast('Error de conexión', 'error');
            }
        };

        // Load initially
        loadContribuyenteData();

        // Update form submission
        const updateForm = document.getElementById('update-form');
        const updateBtn = document.getElementById('update-btn');
        
        updateForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            updateBtn.disabled = true;
            document.getElementById('update-text').textContent = 'Actualizando...';
            document.getElementById('update-spinner').classList.remove('hidden');

            const payload = {
                razon_social: document.getElementById('razon_social').value,
                estado_ruc: document.getElementById('estado_ruc').value,
                tipo_contribuyente: document.getElementById('tipo_contribuyente').value,
                regimen_impositivo: document.getElementById('regimen_impositivo').value,
                actividad_economica: document.getElementById('actividad_economica').value
            };

            try {
                const res = await fetch(`${window.BACKEND_URL}/api/v1/contribuyente/${window.CURRENT_RUC}`, {
                    method: 'PUT',
                    headers: getHeaders(),
                    body: JSON.stringify(payload)
                });
                
                if (res.ok) {
                    const data = await res.json();
                    showToast('Datos actualizados correctamente', 'success');
                    
                    // Update latest update time
                    if (data.ultima_actualizacion) {
                        const date = new Date(data.ultima_actualizacion);
                        document.getElementById('ultima_actualizacion').textContent = date.toLocaleString();
                    }
                    
                    // Update badge
                    const badge = document.getElementById('badge-estado');
                    badge.textContent = data.estado_ruc;
                    if(data.estado_ruc === 'ACTIVO') {
                        badge.className = 'px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800';
                    } else if(data.estado_ruc === 'SUSPENDIDO') {
                        badge.className = 'px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800';
                    } else {
                        badge.className = 'px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800';
                    }

                } else {
                    const errorData = await res.json();
                    showToast(errorData.error || 'Error al actualizar', 'error');
                }
            } catch (err) {
                console.error(err);
                showToast('Error de conexión', 'error');
            } finally {
                updateBtn.disabled = false;
                document.getElementById('update-text').textContent = 'Actualizar Datos';
                document.getElementById('update-spinner').classList.add('hidden');
            }
        });
    }
});
