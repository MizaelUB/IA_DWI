// Estado de la aplicación
const state = {
  veterinaryId: null,
  veterinaryName: null,
  selectedOwner: null,
  selectedPet: null,
  owners: [],
  pets: [],
  appointments: []
};

// Referencias del DOM
const DOM = {
  // Badges y Headers
  activeVetName: document.getElementById('active-vet-name'),
  activeVetBadge: document.getElementById('active-vet-badge'),
  
  // Pasos de Progreso
  progStep1: document.getElementById('prog-step-1'),
  progStep2: document.getElementById('prog-step-2'),
  progStep3: document.getElementById('prog-step-3'),
  
  // Paneles
  panel1: document.getElementById('panel-step-1'),
  panel2: document.getElementById('panel-step-2'),
  panel3: document.getElementById('panel-step-3'),
  panelSuccess: document.getElementById('panel-success'),
  
  // Paso 1
  vetIdInput: document.getElementById('vet-id-input'),
  btnValidateVet: document.getElementById('btn-validate-vet'),
  vetValidationMsg: document.getElementById('vet-validation-message'),
  btnLoadVets: document.getElementById('btn-load-vets'),
  vetGridList: document.getElementById('vet-grid-list'),
  
  // Paso 2
  ownerSearch: document.getElementById('owner-search'),
  ownersList: document.getElementById('owners-scroll-list'),
  petsList: document.getElementById('pets-scroll-list'),
  btnBackTo1: document.getElementById('btn-back-to-1'),
  btnToStep3: document.getElementById('btn-to-step-3'),
  
  // Paso 3
  summaryVet: document.getElementById('summary-vet'),
  summaryOwner: document.getElementById('summary-owner'),
  summaryPet: document.getElementById('summary-pet'),
  appointmentForm: document.getElementById('appointment-form'),
  appointmentDate: document.getElementById('appointment-date'),
  appointmentTime: document.getElementById('appointment-time'),
  appointmentCost: document.getElementById('appointment-cost'),
  appointmentStatus: document.getElementById('appointment-status'),
  appointmentNotes: document.getElementById('appointment-notes'),
  pickupRequested: document.getElementById('pickup-requested'),
  pickupDetailsSection: document.getElementById('pickup-details-section'),
  pickupAddress: document.getElementById('pickup-address'),
  pickupTime: document.getElementById('pickup-time'),
  pickupCost: document.getElementById('pickup-cost'),
  pickupLat: document.getElementById('pickup-lat'),
  pickupLng: document.getElementById('pickup-lng'),
  pickupNotes: document.getElementById('pickup-notes'),
  btnBackTo2: document.getElementById('btn-back-to-2'),
  
  // Pantalla de Éxito
  successDetails: document.getElementById('success-details'),
  btnRestart: document.getElementById('btn-restart'),

  // Listado de Citas
  appointmentsListContainer: document.getElementById('appointments-list-container'),
  btnRefreshAppointments: document.getElementById('btn-refresh-appointments'),
  appointmentsTableBody: document.getElementById('appointments-table-body'),
  hidePastAppointments: document.getElementById('hide-past-appointments')
};

// --- NAVEGACIÓN ---

function goToPanel(step) {
  // Quitar clase active de todos los paneles
  DOM.panel1.classList.remove('active');
  DOM.panel2.classList.remove('active');
  DOM.panel3.classList.remove('active');
  DOM.panelSuccess.classList.remove('active');

  // Quitar clases active/completed de la barra de progreso
  DOM.progStep1.classList.remove('active', 'completed');
  DOM.progStep2.classList.remove('active', 'completed');
  DOM.progStep3.classList.remove('active', 'completed');

  if (step === 1) {
    DOM.panel1.classList.add('active');
    DOM.progStep1.classList.add('active');
    DOM.appointmentsListContainer.style.display = 'none';
  } else if (step === 2) {
    DOM.panel2.classList.add('active');
    DOM.progStep1.classList.add('completed');
    DOM.progStep2.classList.add('active');
    DOM.appointmentsListContainer.style.display = 'block';
  } else if (step === 3) {
    DOM.panel3.classList.add('active');
    DOM.progStep1.classList.add('completed');
    DOM.progStep2.classList.add('completed');
    DOM.progStep3.classList.add('active');
    DOM.appointmentsListContainer.style.display = 'block';
  } else if (step === 'success') {
    DOM.panelSuccess.classList.add('active');
    DOM.progStep1.classList.add('completed');
    DOM.progStep2.classList.add('completed');
    DOM.progStep3.classList.add('completed');
    DOM.appointmentsListContainer.style.display = 'block';
  }
}

// --- PASO 1: VETERINARIA ---

// Validar ID de Veterinaria
async function validateVetId() {
  const vetId = DOM.vetIdInput.value.trim();
  if (!vetId) {
    showValidationMsg('Por favor ingrese un ID válido.', 'error');
    return;
  }

  DOM.btnValidateVet.disabled = true;
  showValidationMsg('Validando ID...', '');

  try {
    const response = await fetch(`/api/veterinarians/${vetId}`);
    const result = await response.json();

    if (response.ok && result.status === 'success') {
      const vet = result.data;
      selectVeterinary(vet.id, vet.name);
      showValidationMsg(`Veterinaria '${vet.name}' validada correctamente. Redireccionando...`, 'success');
      
      setTimeout(() => {
        DOM.vetValidationMsg.style.display = 'none';
        DOM.vetIdInput.value = '';
        goToPanel(2);
        loadOwners();
        loadAppointments();
      }, 1000);
    } else {
      showValidationMsg(result.message || 'La clínica no se encuentra registrada o está inactiva.', 'error');
    }
  } catch (error) {
    showValidationMsg('Error de red al conectar con el servidor.', 'error');
    console.error(error);
  } finally {
    DOM.btnValidateVet.disabled = false;
  }
}

// Mostrar mensajes de validación en Paso 1
function showValidationMsg(text, type) {
  DOM.vetValidationMsg.textContent = text;
  DOM.vetValidationMsg.className = 'message-box';
  if (type) {
    DOM.vetValidationMsg.classList.add(type);
    DOM.vetValidationMsg.style.display = 'block';
  } else if (text) {
    DOM.vetValidationMsg.style.display = 'block';
  } else {
    DOM.vetValidationMsg.style.display = 'none';
  }
}

// Cargar todas las clínicas veterinarias activas
async function loadVeterinaries() {
  DOM.btnLoadVets.disabled = true;
  DOM.vetGridList.innerHTML = '<div class="loading-placeholder">Buscando clínicas en la base de datos...</div>';
  
  try {
    const response = await fetch('/api/veterinarians');
    const result = await response.json();
    
    if (response.ok && result.status === 'success' && result.data.length > 0) {
      DOM.vetGridList.innerHTML = '';
      result.data.forEach(vet => {
        const card = document.createElement('div');
        card.className = 'select-card';
        if (state.veterinaryId === vet.id) {
          card.classList.add('selected');
        }
        
        card.innerHTML = `
          <div class="select-card-info">
            <span class="select-card-title">${vet.name}</span>
            <span class="select-card-subtitle">${vet.city || ''}, ${vet.state || ''}</span>
          </div>
          <span class="select-card-badge">ID: ${vet.id}</span>
        `;
        
        card.addEventListener('click', () => {
          selectVeterinary(vet.id, vet.name);
          card.parentElement.querySelectorAll('.select-card').forEach(c => c.classList.remove('selected'));
          card.classList.add('selected');
          
          setTimeout(() => {
            goToPanel(2);
            loadOwners();
            loadAppointments();
          }, 500);
        });
        
        DOM.vetGridList.appendChild(card);
      });
    } else {
      DOM.vetGridList.innerHTML = '<div class="info-placeholder">No se encontraron clínicas veterinarias activas.</div>';
    }
  } catch (error) {
    DOM.vetGridList.innerHTML = '<div class="message-box error">Error al cargar la lista de veterinarias.</div>';
    console.error(error);
  } finally {
    DOM.btnLoadVets.disabled = false;
  }
}

// Guardar veterinaria seleccionada en el estado
function selectVeterinary(id, name) {
  state.veterinaryId = id;
  state.veterinaryName = name;
  DOM.activeVetName.textContent = name;
  DOM.activeVetBadge.classList.add('active');
}


// --- PASO 2: DUEÑOS Y MASCOTAS ---

// Cargar lista de dueños
async function loadOwners() {
  DOM.ownersList.innerHTML = '<div class="loading-placeholder">Buscando dueños de mascotas...</div>';
  DOM.petsList.innerHTML = '<div class="info-placeholder">Seleccione un dueño de la lista izquierda para ver sus mascotas.</div>';
  DOM.btnToStep3.disabled = true;
  state.selectedOwner = null;
  state.selectedPet = null;

  try {
    const response = await fetch('/api/owners');
    const result = await response.json();
    
    if (response.ok && result.status === 'success') {
      state.owners = result.data;
      renderOwners(state.owners);
    } else {
      DOM.ownersList.innerHTML = '<div class="info-placeholder">Error al consultar los dueños.</div>';
    }
  } catch (error) {
    DOM.ownersList.innerHTML = '<div class="message-box error">Error al conectar con el servidor.</div>';
    console.error(error);
  }
}

// Renderizar la lista de dueños filtrada o completa
function renderOwners(list) {
  if (list.length === 0) {
    DOM.ownersList.innerHTML = '<div class="info-placeholder">No se encontraron dueños que coincidan.</div>';
    return;
  }

  DOM.ownersList.innerHTML = '';
  list.forEach(owner => {
    const card = document.createElement('div');
    card.className = 'select-card';
    if (state.selectedOwner && state.selectedOwner.id === owner.id) {
      card.classList.add('selected');
    }

    card.innerHTML = `
      <div class="select-card-info">
        <span class="select-card-title">${owner.name}</span>
        <span class="select-card-subtitle">${owner.email || 'Sin correo'}</span>
      </div>
      <span class="select-card-badge">ID: ${owner.id}</span>
    `;

    card.addEventListener('click', () => {
      // Remover selección previa
      DOM.ownersList.querySelectorAll('.select-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      
      state.selectedOwner = owner;
      state.selectedPet = null;
      DOM.btnToStep3.disabled = true;
      
      loadPetsForOwner(owner.id);
    });

    DOM.ownersList.appendChild(card);
  });
}

// Cargar mascotas de un dueño seleccionado
async function loadPetsForOwner(ownerId) {
  DOM.petsList.innerHTML = '<div class="loading-placeholder">Cargando mascotas de este cliente...</div>';

  try {
    const response = await fetch(`/api/owners/${ownerId}/pets`);
    const result = await response.json();
    
    if (response.ok && result.status === 'success') {
      state.pets = result.data;
      renderPets(state.pets);
    } else {
      DOM.petsList.innerHTML = '<div class="info-placeholder">Error al consultar las mascotas de este cliente.</div>';
    }
  } catch (error) {
    DOM.petsList.innerHTML = '<div class="message-box error">Error de conexión con el servidor.</div>';
    console.error(error);
  }
}

// Renderizar mascotas en la columna derecha
function renderPets(list) {
  if (list.length === 0) {
    DOM.petsList.innerHTML = '<div class="info-placeholder">Este cliente no tiene mascotas registradas.</div>';
    return;
  }

  DOM.petsList.innerHTML = '';
  list.forEach(pet => {
    const card = document.createElement('div');
    card.className = 'select-card';
    if (state.selectedPet && state.selectedPet.id === pet.id) {
      card.classList.add('selected');
    }

    const breedText = pet.breed ? `, Raza: ${pet.breed}` : '';
    const sexText = pet.sex === 'M' || pet.sex === 'Macho' ? 'Macho' : 'Hembra';

    card.innerHTML = `
      <div class="select-card-info">
        <span class="select-card-title">${pet.name}</span>
        <span class="select-card-subtitle">${pet.specie} (${sexText})${breedText}</span>
      </div>
      <span class="select-card-badge">ID: ${pet.id}</span>
    `;

    card.addEventListener('click', () => {
      DOM.petsList.querySelectorAll('.select-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      
      state.selectedPet = pet;
      DOM.btnToStep3.disabled = false; // Habilitar continuar
    });

    DOM.petsList.appendChild(card);
  });
}


// --- PASO 3: FORMULARIO Y REGISTRO ---

// Preparar los datos antes de mostrar el Paso 3
function prepareAppointmentSummary() {
  DOM.summaryVet.textContent = `${state.veterinaryName} (ID: ${state.veterinaryId})`;
  DOM.summaryOwner.textContent = `${state.selectedOwner.name} (ID: ${state.selectedOwner.id})`;
  DOM.summaryPet.textContent = `${state.selectedPet.name} (${state.selectedPet.specie})`;
  
  // Poner la fecha de hoy por defecto
  const today = new Date().toISOString().split('T')[0];
  DOM.appointmentDate.value = today;
  
  // Poner hora actual redondeada a la siguiente media hora
  const now = new Date();
  let hours = now.getHours();
  let minutes = now.getMinutes();
  if (minutes > 30) {
    hours = (hours + 1) % 24;
    minutes = '00';
  } else if (minutes > 0) {
    minutes = '30';
  } else {
    minutes = '00';
  }
  DOM.appointmentTime.value = `${String(hours).padStart(2, '0')}:${minutes}`;
}

// Crear la cita mediante API POST
async function submitAppointment(event) {
  event.preventDefault();

  const appointmentData = {
    pet_id: state.selectedPet.id,
    user_id: state.selectedOwner.id,
    veterinary_id: state.veterinaryId,
    appointment_date: DOM.appointmentDate.value,
    hour: DOM.appointmentTime.value,
    status: DOM.appointmentStatus.value,
    total_cost: DOM.appointmentCost.value || null,
    notes: DOM.appointmentNotes.value || null,
    pet_name: state.selectedPet.name,
    pickup_requested: DOM.pickupRequested.checked
  };

  if (appointmentData.pickup_requested) {
    appointmentData.pickup_address = DOM.pickupAddress.value || null;
    appointmentData.pickup_time = DOM.pickupTime.value || null;
    appointmentData.pickup_cost = DOM.pickupCost.value || null;
    appointmentData.pickup_latitude = DOM.pickupLat.value || null;
    appointmentData.pickup_longitude = DOM.pickupLng.value || null;
    appointmentData.pickup_notes = DOM.pickupNotes.value || null;
    appointmentData.pickup_status = 'Asignado'; // Estado por defecto del pickup
  }

  const btnSubmit = document.getElementById('btn-submit-appointment');
  btnSubmit.disabled = true;
  const originalText = btnSubmit.innerHTML;
  btnSubmit.innerHTML = 'Procesando registro...';

  try {
    const response = await fetch('/api/appointments', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(appointmentData)
    });

    const result = await response.json();

    if (response.status === 201 && result.status === 'success') {
      showSuccessScreen(result.data.id, appointmentData);
      loadAppointments();
    } else {
      alert(`Error al registrar cita: ${result.message}`);
    }
  } catch (error) {
    console.error(error);
    alert('Error al conectar con el servidor para guardar la cita.');
  } finally {
    btnSubmit.disabled = false;
    btnSubmit.innerHTML = originalText;
  }
}

// Mostrar los datos en la pantalla de éxito
function showSuccessScreen(appointmentId, data) {
  DOM.successDetails.innerHTML = `
    <div class="success-detail-row">
      <span class="success-detail-label">ID de Cita:</span>
      <span class="success-detail-val" style="color: var(--primary); font-weight: 600;">#${appointmentId}</span>
    </div>
    <div class="success-detail-row">
      <span class="success-detail-label">Veterinaria:</span>
      <span class="success-detail-val">${state.veterinaryName}</span>
    </div>
    <div class="success-detail-row">
      <span class="success-detail-label">Mascota:</span>
      <span class="success-detail-val">${state.selectedPet.name} (${state.selectedPet.specie})</span>
    </div>
    <div class="success-detail-row">
      <span class="success-detail-label">Dueño / Cliente:</span>
      <span class="success-detail-val">${state.selectedOwner.name}</span>
    </div>
    <div class="success-detail-row">
      <span class="success-detail-label">Fecha y Hora:</span>
      <span class="success-detail-val">${data.appointment_date} a las ${data.hour} hrs</span>
    </div>
    <div class="success-detail-row">
      <span class="success-detail-label">Costo Estimado:</span>
      <span class="success-detail-val">${data.total_cost ? `$${parseFloat(data.total_cost).toFixed(2)}` : 'No especificado'}</span>
    </div>
    <div class="success-detail-row">
      <span class="success-detail-label">Servicio de Recogida:</span>
      <span class="success-detail-val" style="color: ${data.pickup_requested ? 'var(--success)' : 'var(--text-muted)'}">
        ${data.pickup_requested ? 'Solicitado a domicilio' : 'No solicitado'}
      </span>
    </div>
  `;

  goToPanel('success');
}


// Cargar citas de la veterinaria seleccionada
async function loadAppointments() {
  if (!state.veterinaryId) return;

  DOM.appointmentsTableBody.innerHTML = '<tr><td colspan="9" class="table-placeholder">Cargando citas...</td></tr>';
  DOM.appointmentsListContainer.style.display = 'block';

  try {
    const response = await fetch(`/api/veterinarians/${state.veterinaryId}/appointments`);
    const result = await response.json();

    if (response.ok && result.status === 'success') {
      state.appointments = result.data;
      renderAppointments(state.appointments);
    } else {
      DOM.appointmentsTableBody.innerHTML = `<tr><td colspan="9" class="table-placeholder" style="color: var(--error)">Error al cargar: ${result.message}</td></tr>`;
    }
  } catch (error) {
    console.error(error);
    DOM.appointmentsTableBody.innerHTML = '<tr><td colspan="9" class="table-placeholder" style="color: var(--error)">Error de conexión con el servidor.</td></tr>';
  }
}

// Renderizar las filas de citas
function renderAppointments(list) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  let filteredList = list;
  if (DOM.hidePastAppointments && DOM.hidePastAppointments.checked) {
    filteredList = list.filter(app => {
      const [year, month, day] = app.appointment_date.split('T')[0].split('-').map(Number);
      const appDate = new Date(year, month - 1, day);
      return appDate >= today;
    });
  }

  if (filteredList.length === 0) {
    DOM.appointmentsTableBody.innerHTML = '<tr><td colspan="9" class="table-placeholder">No hay citas agendadas en esta clínica.</td></tr>';
    return;
  }

  DOM.appointmentsTableBody.innerHTML = '';
  filteredList.forEach(app => {
    const tr = document.createElement('tr');

    const formattedDate = new Date(app.appointment_date).toISOString().split('T')[0];
    const formattedTime = app.hour.substring(0, 5);
    const costText = app.total_cost ? `$${parseFloat(app.total_cost).toFixed(2)}` : '-';
    
    // Badge de estado
    const statusLower = app.status.toLowerCase();
    const statusClass = statusLower === 'pendiente' ? 'pendiente' :
                        statusLower === 'confirmada' ? 'confirmada' :
                        statusLower === 'completada' ? 'completada' : 'cancelada';
    
    const transportBadge = app.pickup_requested 
      ? `<span class="badge-transport" title="Recogida solicitada">${app.pickup_status || 'Asignado'}</span>`
      : '<span style="color: var(--text-muted)">-</span>';

    tr.innerHTML = `
      <td style="font-weight: 600; color: var(--primary);">#${app.id}</td>
      <td>
        <strong style="color: var(--text-main);">${app.pet_name || 'Desconocida'}</strong>
        <div style="font-size: 0.75rem; color: var(--text-muted);">${app.pet_specie || ''}</div>
      </td>
      <td>${app.owner_name || 'Desconocido'}</td>
      <td>${formattedDate}</td>
      <td>${formattedTime} hrs</td>
      <td>${costText}</td>
      <td>${transportBadge}</td>
      <td><span class="badge-status ${statusClass}">${app.status}</span></td>
      <td style="font-size: 0.8rem; max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${app.notes || ''}">
        ${app.notes || '<span style="color: var(--text-muted)">Sin notas</span>'}
      </td>
      <td>
        <div style="display: flex; gap: 0.4rem;">
          <button class="btn-action-confirm" onclick="updateAppointmentStatus(${app.id}, 'Confirmada')" title="Confirmar Cita" style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); padding: 0.25rem 0.5rem; border-radius: 4px; cursor: pointer; font-size: 0.75rem; font-weight: 600; transition: all 0.2s;">✓</button>
          <button class="btn-action-reject" onclick="updateAppointmentStatus(${app.id}, 'Cancelada')" title="Rechazar/Cancelar Cita" style="background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); padding: 0.25rem 0.5rem; border-radius: 4px; cursor: pointer; font-size: 0.75rem; font-weight: 600; transition: all 0.2s;">✗</button>
        </div>
      </td>
    `;
    
    DOM.appointmentsTableBody.appendChild(tr);
  });
}

window.updateAppointmentStatus = async (id, status) => {
  try {
    const response = await fetch(`/api/appointments/${id}/status`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ status })
    });
    const result = await response.json();
    if (response.ok && result.status === 'success') {
      loadAppointments();
    } else {
      alert(`Error al actualizar el estado: ${result.message}`);
    }
  } catch (error) {
    console.error(error);
    alert('Error al conectar con el servidor.');
  }
};


// --- EVENT LISTENERS ---

function initEventListeners() {
  // Paso 1
  DOM.btnValidateVet.addEventListener('click', validateVetId);
  DOM.vetIdInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') validateVetId();
  });
  DOM.btnLoadVets.addEventListener('click', loadVeterinaries);

  // Paso 2
  DOM.ownerSearch.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase().trim();
    if (!query) {
      renderOwners(state.owners);
    } else {
      const filtered = state.owners.filter(owner => 
        owner.name.toLowerCase().includes(query) || 
        (owner.email && owner.email.toLowerCase().includes(query)) ||
        (owner.phone_number && owner.phone_number.includes(query))
      );
      renderOwners(filtered);
    }
  });

  DOM.btnBackTo1.addEventListener('click', () => {
    goToPanel(1);
  });

  DOM.btnToStep3.addEventListener('click', () => {
    if (state.selectedOwner && state.selectedPet) {
      prepareAppointmentSummary();
      goToPanel(3);
    }
  });

  // Paso 3
  DOM.pickupRequested.addEventListener('change', (e) => {
    if (e.target.checked) {
      DOM.pickupDetailsSection.style.display = 'block';
    } else {
      DOM.pickupDetailsSection.style.display = 'none';
    }
  });

  DOM.btnBackTo2.addEventListener('click', () => {
    goToPanel(2);
  });

  DOM.appointmentForm.addEventListener('submit', submitAppointment);

  // Éxito
  DOM.btnRestart.addEventListener('click', () => {
    // Resetear formulario y estados pero manteniendo la veterinaria seleccionada
    DOM.appointmentForm.reset();
    DOM.pickupDetailsSection.style.display = 'none';
    DOM.ownerSearch.value = '';
    
    // Regresar al paso 2 con la veterinaria actual
    goToPanel(2);
    loadOwners();
    loadAppointments();
  });

  DOM.btnRefreshAppointments.addEventListener('click', loadAppointments);
  DOM.hidePastAppointments.addEventListener('change', () => {
    renderAppointments(state.appointments);
  });
}

// Iniciar aplicación
document.addEventListener('DOMContentLoaded', () => {
  initEventListeners();
  goToPanel(1);
});
