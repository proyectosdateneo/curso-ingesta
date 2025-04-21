-- Creación de tablas para el sistema de gestión de cursos de formación

-- Tabla de clientes
CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR NOT NULL,
    dominio VARCHAR,
    descripcion TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de cursos
CREATE TABLE cursos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR NOT NULL,
    descripcion TEXT,
    duracion_horas INTEGER,
    precio_base DECIMAL(10,2)
);

-- Tabla de ventas
CREATE TABLE ventas (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(id),
    curso_id INTEGER REFERENCES cursos(id),
    fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_inicio TIMESTAMP,
    fecha_fin TIMESTAMP,
    num_participantes INTEGER,
    precio_total DECIMAL(10,2),
    estado VARCHAR DEFAULT 'programado',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger para actualizar updated_at en ventas
CREATE OR REPLACE FUNCTION update_ventas_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ventas_updated_at_trigger
    BEFORE UPDATE ON ventas
    FOR EACH ROW
    EXECUTE FUNCTION update_ventas_updated_at();

-- Tabla de participantes
CREATE TABLE participantes (
    id SERIAL PRIMARY KEY,
    venta_id INTEGER REFERENCES ventas(id),
    nombre VARCHAR NOT NULL,
    apellido VARCHAR NOT NULL,
    email VARCHAR,
    calificacion INTEGER
);

-- Tabla de actividades de participantes
CREATE TABLE actividades_participantes (
    id SERIAL PRIMARY KEY,
    participante_id INTEGER REFERENCES participantes(id),
    tipo_actividad VARCHAR,
    contenido_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    detalles VARCHAR
);

-- Índices para mejorar el rendimiento
CREATE INDEX idx_ventas_cliente_id ON ventas(cliente_id);
CREATE INDEX idx_ventas_curso_id ON ventas(curso_id);
CREATE INDEX idx_participantes_venta_id ON participantes(venta_id);
CREATE INDEX idx_actividades_participante_id ON actividades_participantes(participante_id);
CREATE INDEX idx_actividades_timestamp ON actividades_participantes(timestamp); 