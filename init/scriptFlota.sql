-- Configurar charset a UTF-8 para soportar acentos correctamente
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET COLLATION_CONNECTION=utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS flota_logistica CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE flota_logistica;

CREATE TABLE usuario (
    id_usuario INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50) COLLATE utf8mb4_unicode_ci,
    correo VARCHAR(50) UNIQUE COLLATE utf8mb4_unicode_ci,
    password VARCHAR(128),
    rol VARCHAR(20) COLLATE utf8mb4_unicode_ci
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO usuario (nombre, correo, password, rol) VALUES
('Admin Principal', 'admin@correo.com', 'admin123', 'admin'),
('Mecánico Juan', 'mecanico@correo.com', 'mecanico123', 'mecanico');

CREATE TABLE vehiculo (
    id_vehiculo INT PRIMARY KEY AUTO_INCREMENT,
    matricula VARCHAR(20) UNIQUE NOT NULL COLLATE utf8mb4_unicode_ci,
    modelo VARCHAR(50) NOT NULL COLLATE utf8mb4_unicode_ci,
    tipo VARCHAR(30) NOT NULL COLLATE utf8mb4_unicode_ci,
    capacidad INT NOT NULL,
    marca VARCHAR(30) NOT NULL COLLATE utf8mb4_unicode_ci,
    estado VARCHAR(15) NOT NULL COLLATE utf8mb4_unicode_ci,
    kilometraje INT NOT NULL
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO vehiculo (matricula, modelo, tipo, capacidad, marca, estado, kilometraje) VALUES
('ABC123', 'Sprinter 2020', 'Camioneta', 1000, 'Mercedes-Benz', 'activo', 25000),
('XYZ789', 'Transit 2018', 'Furgoneta', 800, 'Ford', 'mantenimiento', 74000),
('DEF456', 'Hilux 2022', 'Camioneta', 1200, 'Toyota', 'activo', 15000),
('GHI789', 'Freightliner 2021', 'Camión', 5000, 'Freightliner', 'activo', 50000),
('JKL012', 'Versa 2023', 'Sedán', 500, 'Nissan', 'activo', 8000),
('MNO345', 'Kenworth 2020', 'Camión', 4500, 'Kenworth', 'inactivo', 120000),
('PQR678', 'RAV4 2021', 'SUV', 700, 'Toyota', 'activo', 35000),
('STU901', 'Volvo 2019', 'Camión', 5500, 'Volvo', 'activo', 95000),
('VWX234', 'Aveo 2022', 'Sedán', 450, 'Chevrolet', 'activo', 12000),
('YZA567', 'CX-5 2020', 'SUV', 650, 'Mazda', 'mantenimiento', 42000),
('BCD890', 'Doblado 2019', 'Furgoneta', 750, 'Hyundai', 'activo', 88000),
('EFG123', 'Tacoma 2021', 'Camioneta', 950, 'Toyota', 'activo', 22000),
('HIJ456', 'F-150 2020', 'Camioneta', 1100, 'Ford', 'activo', 60000),
('KLM789', 'Fortuner 2022', 'SUV', 800, 'Toyota', 'activo', 18000),
('NOP012', 'Ranger 2021', 'Camioneta', 900, 'Ford', 'inactivo', 45000);

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
('Isabella', 'García', '5556232345', 'Calle Doce 909, Merida', '1989-08-03');

CREATE TABLE viaje (
    id_viaje INT PRIMARY KEY AUTO_INCREMENT,
    origen VARCHAR(50) COLLATE utf8mb4_unicode_ci,
    destino VARCHAR(50) COLLATE utf8mb4_unicode_ci,
    fecha_salida DATE,
    estado VARCHAR(20) COLLATE utf8mb4_unicode_ci
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO viaje (origen, destino, fecha_salida, estado) VALUES
('CDMX', 'Puebla', '2024-06-01', 'completado'),
('Querétaro', 'León', '2024-06-02', 'en progreso'),
('CDMX', 'Guadalajara', '2024-06-03', 'completado'),
('Monterrey', 'CDMX', '2024-06-04', 'completado'),
('CDMX', 'Veracruz', '2024-06-05', 'en progreso'),
('Cancún', 'Playa del Carmen', '2024-06-06', 'completado'),
('CDMX', 'Toluca', '2024-06-07', 'completado'),
('Tijuana', 'CDMX', '2024-06-08', 'pendiente'),
('CDMX', 'Acapulco', '2024-06-09', 'en progreso'),
('San Luis Potosí', 'CDMX', '2024-06-10', 'completado'),
('CDMX', 'Mérida', '2024-06-11', 'completado'),
('Guadalajara', 'Monterrey', '2024-06-12', 'en progreso'),
('CDMX', 'Cuernavaca', '2024-06-13', 'completado'),
('León', 'Querétaro', '2024-06-14', 'en progreso'),
('CDMX', 'Taxco', '2024-06-15', 'completado');

CREATE TABLE mantenimiento (
    id_mantenimiento INT PRIMARY KEY AUTO_INCREMENT,
    id_vehiculo INT,
    descripcion VARCHAR(255) COLLATE utf8mb4_unicode_ci,
    fecha DATE,
    FOREIGN KEY (id_vehiculo) REFERENCES vehiculo(id_vehiculo) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO mantenimiento (id_vehiculo, descripcion, fecha) VALUES
(1, 'Cambio de aceite y filtro', '2024-05-20'),
(2, 'Reparación de frenos', '2024-05-30'),
(3, 'Revisión de suspensión', '2024-06-01'),
(4, 'Cambio de llantas', '2024-06-05'),
(5, 'Reparación de transmisión', '2024-06-10'),
(6, 'Mantenimiento preventivo general', '2024-06-12'),
(7, 'Revisión de sistema eléctrico', '2024-06-15'),
(8, 'Cambio de aceite', '2024-06-18'),
(9, 'Reparación de radiador', '2024-06-20'),
(10, 'Revisión de motor', '2024-06-22'),
(1, 'Limpieza de inyectores', '2024-06-25'),
(3, 'Cambio de batería', '2024-06-28');

CREATE TABLE consumo (
    id_consumo INT PRIMARY KEY AUTO_INCREMENT,
    id_vehiculo INT,
    litros DECIMAL(10,2),
    fecha DATE,
    FOREIGN KEY (id_vehiculo) REFERENCES vehiculo(id_vehiculo) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO consumo (id_vehiculo, litros, fecha) VALUES
(1, 60.0, '2024-06-01'),
(2, 55.5, '2024-06-02'),
(3, 48.0, '2024-06-03'),
(4, 120.5, '2024-06-04'),
(5, 35.0, '2024-06-05'),
(6, 110.0, '2024-06-06'),
(7, 52.5, '2024-06-07'),
(8, 115.0, '2024-06-08'),
(9, 40.0, '2024-06-09'),
(10, 58.0, '2024-06-10'),
(1, 62.5, '2024-06-11'),
(3, 50.0, '2024-06-12'),
(5, 38.5, '2024-06-13'),
(7, 55.0, '2024-06-14'),
(9, 42.0, '2024-06-15');

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

CREATE TABLE incidente (
    id_incidente INT PRIMARY KEY AUTO_INCREMENT,
    id_vehiculo INT,
    tipo VARCHAR(50) COLLATE utf8mb4_unicode_ci,
    fecha DATE,
    descripcion VARCHAR(255) COLLATE utf8mb4_unicode_ci,
    FOREIGN KEY (id_vehiculo) REFERENCES vehiculo(id_vehiculo) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO incidente (id_vehiculo, tipo, fecha, descripcion) VALUES
(1, 'accidente', '2024-06-01', 'Pequeño choque en caseta'),
(2, 'infracción', '2024-06-02', 'Exceso de velocidad detectado'),
(3, 'daño', '2024-06-03', 'Espejo lateral roto'),
(4, 'accidente', '2024-06-04', 'Choque trasero en tráfico'),
(5, 'infracción', '2024-06-05', 'Estacionamiento indebido'),
(6, 'daño', '2024-06-06', 'Defecto en llantas'),
(7, 'retraso', '2024-06-07', 'Demora de 2 horas en entrega'),
(8, 'accidente', '2024-06-08', 'Impacto con poste'),
(9, 'infracción', '2024-06-09', 'Luz roja cruzada'),
(10, 'daño', '2024-06-10', 'Sensor de proximidad dañado'),
(1, 'retraso', '2024-06-11', 'Atasco vehicular'),
(3, 'infracción', '2024-06-12', 'Documentación vencida');

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
