SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET COLLATION_CONNECTION=utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS flota_logistica CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE flota_logistica;

-- =====================================================
-- TABLA FLOTA
-- =====================================================

CREATE TABLE flota (
    id_flota INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(40) COLLATE utf8mb4_unicode_ci,
    descripcion VARCHAR(100) COLLATE utf8mb4_unicode_ci
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO flota (nombre, descripcion) VALUES
('Flota Norte', 'Vehículos de la zona Norte'),
('Flota Sur', 'Vehículos de la zona Sur'),
('Flota Centro', 'Vehículos de la zona Centro'),
('Flota Especial', 'Vehículos para carga pesada');


-- =====================================================
-- USUARIOS
-- =====================================================
CREATE TABLE usuario (
    id_usuario INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL,
    correo VARCHAR(50) UNIQUE COLLATE utf8mb4_unicode_ci NOT NULL,
    password VARCHAR(128) NOT NULL,
    rol ENUM('admin', 'mecanico', 'logistica', 'conductor', 'observador')
        NOT NULL COLLATE utf8mb4_unicode_ci
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO usuario (nombre, correo, password, rol) VALUES
('Admin Principal', 'admin@correo.com', 'admin123', 'admin'),
('Mecánico Juan', 'mecanico@correo.com', 'mecanico123', 'mecanico'),
('Pedro Ramírez', 'conductor@correo.com', 'conductor123', 'conductor'),
('Carlos López', 'logistica@correo.com', 'logistica123', 'logistica'),
('Laura Martínez', 'observador@correo.com', 'observador123', 'observador');

-- =====================================================
-- CONDUCTOR
-- =====================================================

CREATE TABLE conductor (
    id_conductor INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(60) NOT NULL COLLATE utf8mb4_unicode_ci,
    apellido VARCHAR(60) NOT NULL COLLATE utf8mb4_unicode_ci,
    telefono VARCHAR(20) COLLATE utf8mb4_unicode_ci,
    direccion VARCHAR(100) COLLATE utf8mb4_unicode_ci,
    fecha_nacimiento DATE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO conductor (nombre, apellido, telefono, direccion, fecha_nacimiento) VALUES
('Pedro', 'Ramírez', '5555121234', 'Calle Uno 123, CDMX', '1980-06-10'),
('María', 'Sosa', '5556232345', 'Calle Dos 456, Puebla', '1985-12-15'),
('Carlos', 'Gómez', '5557343456', 'Calle Tres 789, Querétaro', '1982-03-22'),
('Ana', 'Torres', '5558454567', 'Calle Cuatro 101, Guadalajara', '1988-07-30'),
('Luis', 'Fernández', '5559565678', 'Calle Cinco 202, Monterrey', '1979-11-05'),
('Laura', 'Díaz', '5550676789', 'Calle Seis 303, Veracruz', '1990-01-14'),
('José', 'Martínez', '5551787890', 'Calle Siete 404, León', '1984-09-20'),
('Marta', 'Sánchez', '5552898901', 'Calle Ocho 505, Cancún', '1987-04-11'),
('Andrés', 'Hernández', '5553909012', 'Calle Nueve 606, Acapulco', '1983-10-25'),
('Lucía', 'Mendoza', '5554010123', 'Calle Diez 707, Tijuana', '1991-02-08'),
('Francisco', 'López', '5555121234', 'Calle Once 808, San Luis Potosí', '1981-05-17'),
('Isabella', 'García', '5556232345', 'Calle Doce 909', '1989-08-03');

ALTER TABLE conductor
    ADD COLUMN id_usuario INT NULL;
ALTER TABLE conductor
    ADD CONSTRAINT fk_conductor_usuario
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
    ON DELETE SET NULL;

UPDATE conductor c
JOIN usuario u ON u.nombre = CONCAT(c.nombre,' ',c.apellido) AND u.rol = 'conductor'
SET c.id_usuario = u.id_usuario;


-- =====================================================
-- VEHÍCULO (CON FK A FLOTA)
-- =====================================================

CREATE TABLE vehiculo (
    id_vehiculo INT PRIMARY KEY AUTO_INCREMENT,
    matricula VARCHAR(20) UNIQUE NOT NULL COLLATE utf8mb4_unicode_ci,
    modelo VARCHAR(50) NOT NULL COLLATE utf8mb4_unicode_ci,
    tipo VARCHAR(30) NOT NULL COLLATE utf8mb4_unicode_ci,
    capacidad INT NOT NULL,
    marca VARCHAR(30) NOT NULL COLLATE utf8mb4_unicode_ci,
    estado VARCHAR(15) NOT NULL COLLATE utf8mb4_unicode_ci,
    kilometraje INT NOT NULL,
    id_flota INT,
    CONSTRAINT fk_vehiculo_flota
        FOREIGN KEY (id_flota) REFERENCES flota(id_flota)
        ON DELETE SET NULL
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO vehiculo (matricula, modelo, tipo, capacidad, marca, estado, kilometraje, id_flota) VALUES
('ABC123', 'Sprinter 2020',   'Camioneta', 1000, 'Mercedes-Benz', 'activo',       25000, 3),
('XYZ789', 'Transit 2018',    'Furgoneta',  800, 'Ford',          'mantenimiento',74000, 3),
('DEF456', 'Hilux 2022',      'Camioneta', 1200, 'Toyota',        'activo',       15000, 1),
('GHI789', 'Freightliner 2021','Camión',   5000, 'Freightliner',  'activo',       50000, 4),
('JKL012', 'Versa 2023',      'Sedán',      500, 'Nissan',        'activo',        8000, 2),
('MNO345', 'Kenworth 2020',   'Camión',    4500, 'Kenworth',      'inactivo',    120000, 4),
('PQR678', 'RAV4 2021',       'SUV',        700, 'Toyota',        'activo',       35000, 1),
('STU901', 'Volvo 2019',      'Camión',    5500, 'Volvo',         'activo',       95000, 4),
('VWX234', 'Aveo 2022',       'Sedán',      450, 'Chevrolet',     'activo',       12000, 2),
('YZA567', 'CX-5 2020',       'SUV',        650, 'Mazda',         'mantenimiento',42000, 1),
('BCD890', 'Doblado 2019',    'Furgoneta',  750, 'Hyundai',       'activo',       88000, 3),
('EFG123', 'Tacoma 2021',     'Camioneta',  950, 'Toyota',        'activo',       22000, 1),
('HIJ456', 'F-150 2020',      'Camioneta', 1100, 'Ford',          'activo',       60000, 1),
('KLM789', 'Fortuner 2022',   'SUV',        800, 'Toyota',        'activo',       18000, 1),
('NOP012', 'Ranger 2021',     'Camioneta',  900, 'Ford',          'inactivo',     45000, 1);

-- =====================================================
-- ORDEN DE SERVICIO
-- =====================================================

CREATE TABLE orden_servicio (
    id_orden INT PRIMARY KEY AUTO_INCREMENT,
    descripcion VARCHAR(255) COLLATE utf8mb4_unicode_ci,
    fecha DATE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO orden_servicio (descripcion, fecha) VALUES
('Paquete refrigerado', '2024-06-01'),
('Material industrial', '2024-06-02'),
('Entrega de documentos', '2024-06-03'),
('Carga de mercancía', '2024-06-04'),
('Mudanza residencial', '2024-06-05'),
('Transporte de valores', '2024-06-06'),
('Envío de repuestos', '2024-06-07'),
('Carga de construcción', '2024-06-08'),
('Entrega de alimentos', '2024-06-09'),
('Transporte de equipos', '2024-06-10'),
('Logística de eventos', '2024-06-11'),
('Entrega urgente', '2024-06-12'),
('Carga consolidada', '2024-06-13'),
('Transporte de medicamentos', '2024-06-14'),
('Entregas en zona metropolitana', '2024-06-15');

-- =====================================================
-- VIAJE (CON FK A VEHÍCULO, CONDUCTOR Y ORDEN)
-- =====================================================

CREATE TABLE viaje (
    id_viaje INT PRIMARY KEY AUTO_INCREMENT,
    origen VARCHAR(50) COLLATE utf8mb4_unicode_ci,
    destino VARCHAR(50) COLLATE utf8mb4_unicode_ci,
    fecha_salida DATE,
    estado VARCHAR(20) COLLATE utf8mb4_unicode_ci,
    id_vehiculo INT,
    id_conductor INT,
    id_orden INT,
    CONSTRAINT fk_viaje_vehiculo
        FOREIGN KEY (id_vehiculo) REFERENCES vehiculo(id_vehiculo)
        ON DELETE SET NULL,
    CONSTRAINT fk_viaje_conductor
        FOREIGN KEY (id_conductor) REFERENCES conductor(id_conductor)
        ON DELETE SET NULL,
    CONSTRAINT fk_viaje_orden
        FOREIGN KEY (id_orden) REFERENCES orden_servicio(id_orden)
        ON DELETE SET NULL
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO viaje (origen, destino, fecha_salida, estado, id_vehiculo, id_conductor, id_orden) VALUES
('CDMX',           'Puebla',        '2024-06-01', 'completado',  1,  1,  1),
('Querétaro',      'León',          '2024-06-02', 'en progreso', 2,  2,  2),
('CDMX',           'Guadalajara',   '2024-06-03', 'completado',  3,  3,  3),
('Monterrey',      'CDMX',          '2024-06-04', 'completado',  4,  4,  4),
('CDMX',           'Veracruz',      '2024-06-05', 'en progreso', 5,  5,  5),
('Cancún',         'Playa del Carmen', '2024-06-06','completado',6,  6,  6),
('CDMX',           'Toluca',        '2024-06-07', 'completado',  7,  7,  7),
('Tijuana',        'CDMX',          '2024-06-08', 'pendiente',   8,  8,  8),
('CDMX',           'Acapulco',      '2024-06-09', 'en progreso', 9,  9,  9),
('San Luis Potosí','CDMX',          '2024-06-10', 'completado',  10, 10, 10),
('CDMX',           'Mérida',        '2024-06-11', 'completado',  1, 11, 11),
('Guadalajara',    'Monterrey',     '2024-06-12', 'en progreso', 2, 12, 12),
('CDMX',           'Cuernavaca',    '2024-06-13', 'completado',  3,  1, 13),
('León',           'Querétaro',     '2024-06-14', 'en progreso', 4,  2, 14),
('CDMX',           'Taxco',         '2024-06-15', 'completado',  5,  3, 15);

-- =====================================================
-- MANTENIMIENTO
-- =====================================================

CREATE TABLE mantenimiento (
    id_mantenimiento INT PRIMARY KEY AUTO_INCREMENT,
    id_vehiculo INT NOT NULL,
    tipo ENUM('preventivo','correctivo','reparacion') 
        COLLATE utf8mb4_unicode_ci NOT NULL,
    descripcion VARCHAR(255) COLLATE utf8mb4_unicode_ci NOT NULL,
    costo DECIMAL(10,2) NOT NULL,
    fecha DATE NOT NULL,
    FOREIGN KEY (id_vehiculo) REFERENCES vehiculo(id_vehiculo)
        ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO mantenimiento (id_vehiculo, tipo, descripcion, costo, fecha) VALUES
(1, 'preventivo', 'Cambio de aceite y filtro', 850.00, '2024-05-20'),
(2, 'reparacion', 'Reparación de frenos', 2800.00, '2024-05-30'),
(3, 'reparacion', 'Revisión de suspensión y cambio de bujes', 4200.00, '2024-06-01'),
(4, 'reparacion', 'Cambio de llanta trasera', 1800.00, '2024-06-05'),
(5, 'reparacion', 'Reparación de transmisión', 9500.00, '2024-06-10'),
(6, 'preventivo', 'Servicio general', 1200.00, '2024-06-12');

-- =====================================================
-- CONSUMO
-- =====================================================

CREATE TABLE consumo (
    id_consumo INT PRIMARY KEY AUTO_INCREMENT,
    matricula VARCHAR(20) COLLATE utf8mb4_unicode_ci,
    litros DECIMAL(10,2),
    fecha DATE,
    FOREIGN KEY (matricula) REFERENCES vehiculo(matricula) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO consumo (matricula, litros, fecha) VALUES
('ABC123', 60.0, '2024-06-01'),
('XYZ789', 55.5, '2024-06-02'),
('DEF456', 48.0, '2024-06-03'),
('GHI789', 120.5, '2024-06-04'),
('JKL012', 35.0, '2024-06-05'),
('MNO345', 110.0, '2024-06-06'),
('PQR678', 52.5, '2024-06-07'),
('STU901', 115.0, '2024-06-08'),
('VWX234', 40.0, '2024-06-09'),
('YZA567', 58.0, '2024-06-10'),
('ABC123', 62.5, '2024-06-11'),
('DEF456', 50.0, '2024-06-12'),
('JKL012', 38.5, '2024-06-13'),
('PQR678', 55.0, '2024-06-14'),
('VWX234', 42.0, '2024-06-15');

-- =====================================================
-- INCIDENTE
-- =====================================================

CREATE TABLE incidente (
    id_incidente INT PRIMARY KEY AUTO_INCREMENT,
    matricula VARCHAR(20) COLLATE utf8mb4_unicode_ci,
    tipo VARCHAR(50) COLLATE utf8mb4_unicode_ci,
    fecha DATE,
    descripcion VARCHAR(255) COLLATE utf8mb4_unicode_ci,
    FOREIGN KEY (matricula) REFERENCES vehiculo(matricula) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO incidente (matricula, tipo, fecha, descripcion) VALUES
('ABC123', 'accidente', '2024-06-01', 'Pequeño choque en caseta'),
('XYZ789', 'infracción', '2024-06-02', 'Exceso de velocidad detectado'),
('DEF456', 'daño', '2024-06-03', 'Espejo lateral roto'),
('GHI789', 'accidente', '2024-06-04', 'Choque trasero en tráfico'),
('JKL012', 'infracción', '2024-06-05', 'Estacionamiento indebido'),
('MNO345', 'daño', '2024-06-06', 'Defecto en llantas'),
('PQR678', 'retraso', '2024-06-07', 'Demora de 2 horas en entrega'),
('STU901', 'accidente', '2024-06-08', 'Impacto con poste'),
('VWX234', 'infracción', '2024-06-09', 'Luz roja cruzada'),
('YZA567', 'daño', '2024-06-10', 'Sensor de proximidad dañado'),
('ABC123', 'retraso', '2024-06-11', 'Atasco vehicular'),
('DEF456', 'infracción', '2024-06-12', 'Documentación vencida');

-- =====================================================
-- LICENCIA (cada conductor puede tener 1..N licencias)
-- =====================================================

CREATE TABLE licencia (
    id_licencia INT PRIMARY KEY AUTO_INCREMENT,
    id_conductor INT NOT NULL,
    tipo VARCHAR(30) COLLATE utf8mb4_unicode_ci NOT NULL,
    fecha_emision DATE NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    FOREIGN KEY (id_conductor) REFERENCES conductor(id_conductor)
        ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO licencia (id_conductor, tipo, fecha_emision, fecha_vencimiento) VALUES
(1, 'A', '2020-01-01', '2025-01-01'),
(1, 'B', '2022-06-01', '2027-06-01'),
(2, 'A', '2019-03-15', '2024-03-15'),
(3, 'C', '2021-09-10', '2026-09-10');

-- =====================================================
-- EVALUACION (evaluaciones a usuarios del sistema)
-- =====================================================

CREATE TABLE evaluacion (
    id_evaluacion INT PRIMARY KEY AUTO_INCREMENT,
    id_usuario INT NOT NULL,
    fecha DATE NOT NULL,
    puntuacion INT NOT NULL,           -- por ejemplo 1–10
    comentarios VARCHAR(255) COLLATE utf8mb4_unicode_ci,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
        ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO evaluacion (id_usuario, fecha, puntuacion, comentarios) VALUES
(3, '2024-05-10', 9, 'Conductor puntual y cuidadoso con el vehículo'),
(2, '2024-05-12', 8, 'Mecánico con buen tiempo de respuesta'),
(4, '2024-05-15', 9, 'Área de logística organiza bien las rutas');