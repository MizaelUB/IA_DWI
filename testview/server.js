import express from 'express';
import pg from 'pg';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Cargar .env de la raíz
dotenv.config({ path: path.join(__dirname, '../.env') });

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const { Pool } = pg;

const pool = new Pool({
  database: process.env.DB_DATABASE || 'postgres',
  host: process.env.DB_HOST || 'aws-0-us-east-1.pooler.supabase.com',
  port: parseInt(process.env.DB_PORT || '5432', 10),
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || '',
  ssl: {
    rejectUnauthorized: false
  }
});

// Endpoint: Obtener lista de veterinarias activas
app.get('/api/veterinarians', async (req, res) => {
  try {
    const query = `
      SELECT id, name, city, state, phone_number, email 
      FROM veterinary 
      WHERE is_active = TRUE 
      ORDER BY id ASC;
    `;
    const { rows } = await pool.query(query);
    res.json({ status: 'success', data: rows });
  } catch (error) {
    console.error('Error fetching veterinarians:', error);
    res.status(500).json({ status: 'error', message: error.message });
  }
});

// Endpoint: Obtener veterinaria por ID
app.get('/api/veterinarians/:id', async (req, res) => {
  const { id } = req.params;
  try {
    const query = `
      SELECT id, name, city, state, phone_number, email 
      FROM veterinary 
      WHERE id = $1 AND is_active = TRUE;
    `;
    const { rows } = await pool.query(query, [id]);
    if (rows.length === 0) {
      return res.status(404).json({ status: 'error', message: 'Veterinaria no encontrada o inactiva' });
    }
    res.json({ status: 'success', data: rows[0] });
  } catch (error) {
    console.error(`Error fetching veterinarian ${id}:`, error);
    res.status(500).json({ status: 'error', message: error.message });
  }
});

// Endpoint: Obtener dueños de mascotas
app.get('/api/owners', async (req, res) => {
  try {
    const query = `
      SELECT id, name, email, phone_number 
      FROM users_app 
      ORDER BY name ASC;
    `;
    const { rows } = await pool.query(query);
    res.json({ status: 'success', data: rows });
  } catch (error) {
    console.error('Error fetching owners:', error);
    res.status(500).json({ status: 'error', message: error.message });
  }
});

// Endpoint: Obtener mascotas de un dueño específico
app.get('/api/owners/:id/pets', async (req, res) => {
  const { id } = req.params;
  try {
    const query = `
      SELECT id, name, specie, breed, sex, age, weight 
      FROM pets 
      WHERE user_id = $1 
      ORDER BY name ASC;
    `;
    const { rows } = await pool.query(query, [id]);
    res.json({ status: 'success', data: rows });
  } catch (error) {
    console.error(`Error fetching pets for owner ${id}:`, error);
    res.status(500).json({ status: 'error', message: error.message });
  }
});

// Endpoint: Crear una cita veterinaria
app.post('/api/appointments', async (req, res) => {
  const {
    pet_id,
    user_id,
    veterinary_id,
    appointment_date,
    hour,
    status = 'Pendiente',
    total_cost,
    notes,
    pickup_requested = false,
    pickup_address = null,
    pickup_latitude = null,
    pickup_longitude = null,
    pickup_time = null,
    pickup_status = null,
    pickup_notes = null,
    pickup_cost = null,
    pet_name
  } = req.body;

  // Validaciones básicas de campos obligatorios
  if (!pet_id || !user_id || !veterinary_id || !appointment_date || !hour) {
    return res.status(400).json({
      status: 'error',
      message: 'Los campos pet_id, user_id, veterinary_id, appointment_date y hour son obligatorios.'
    });
  }

  try {
    const insertQuery = `
      INSERT INTO appointments (
        pet_id, 
        user_id, 
        veterinary_id, 
        appointment_date, 
        hour, 
        status,
        total_cost, 
        notes, 
        pickup_requested, 
        pickup_address,
        pickup_latitude, 
        pickup_longitude, 
        pickup_time, 
        pickup_status,
        pickup_notes, 
        pickup_cost, 
        pet_name
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17
      ) RETURNING id;
    `;

    const values = [
      pet_id,
      user_id,
      veterinary_id,
      appointment_date,
      hour,
      status,
      total_cost ? parseFloat(total_cost) : null,
      notes,
      pickup_requested,
      pickup_address,
      pickup_latitude ? parseFloat(pickup_latitude) : null,
      pickup_longitude ? parseFloat(pickup_longitude) : null,
      pickup_time,
      pickup_status,
      pickup_notes,
      pickup_cost ? parseFloat(pickup_cost) : null,
      pet_name
    ];

    const { rows } = await pool.query(insertQuery, values);
    res.status(201).json({
      status: 'success',
      message: 'Cita creada exitosamente.',
      data: { id: rows[0].id }
    });
  } catch (error) {
    console.error('Error creating appointment:', error);
    res.status(500).json({ status: 'error', message: error.message });
  }
});

// Endpoint: Obtener lista de citas de una veterinaria específica
app.get('/api/veterinarians/:id/appointments', async (req, res) => {
  const { id } = req.params;
  try {
    const query = `
      SELECT 
        a.id, 
        a.pet_id,
        a.user_id,
        a.veterinary_id,
        a.appointment_date, 
        a.hour, 
        a.status, 
        a.total_cost, 
        a.notes,
        a.pickup_requested,
        a.pickup_status,
        a.pet_name,
        u.name as owner_name,
        p.specie as pet_specie
      FROM appointments a
      LEFT JOIN users_app u ON a.user_id = u.id
      LEFT JOIN pets p ON a.pet_id = p.id
      WHERE a.veterinary_id = $1
      ORDER BY a.appointment_date DESC, a.hour DESC;
    `;
    const { rows } = await pool.query(query, [id]);
    res.json({ status: 'success', data: rows });
  } catch (error) {
    console.error(`Error fetching appointments for veterinary ${id}:`, error);
    res.status(500).json({ status: 'error', message: error.message });
  }
});

// Endpoint: Actualizar el estado de una cita
app.patch('/api/appointments/:id/status', async (req, res) => {
  const { id } = req.params;
  const { status } = req.body;
  
  if (!status) {
    return res.status(400).json({ status: 'error', message: 'El campo status es obligatorio.' });
  }

  try {
    const query = `
      UPDATE appointments 
      SET status = $1, updated_at = CURRENT_TIMESTAMP
      WHERE id = $2
      RETURNING id;
    `;
    const { rows } = await pool.query(query, [status, id]);
    if (rows.length === 0) {
      return res.status(404).json({ status: 'error', message: 'Cita no encontrada.' });
    }
    res.json({ status: 'success', message: `Estado de la cita ${id} actualizado a ${status}.` });
  } catch (error) {
    console.error(`Error updating status for appointment ${id}:`, error);
    res.status(500).json({ status: 'error', message: error.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Servidor escuchando en http://localhost:${PORT}`);
});
