-- Script organizado y con datos de ejemplo que cubren todos los valores enum/posibles
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET COLLATION_CONNECTION=utf8mb4_unicode_ci;

DROP DATABASE IF EXISTS flota_logistica;
CREATE DATABASE flota_logistica CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE flota_logistica;

-- =====================================================
-- FLOTA
-- =====================================================
CREATE TABLE flota (
    id_flota INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(40) COLLATE utf8mb4_unicode_ci,
    descripcion VARCHAR(100) COLLATE utf8mb4_unicode_ci
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO flota (id_flota, nombre, descripcion) VALUES
(1,'Flota Norte','Vehículos de la zona Norte'),
(2,'Flota Sur','Vehículos de la zona Sur'),
(3,'Flota Centro','Vehículos de la zona Centro'),
(4,'Flota Especial','Vehículos para carga pesada');

-- =====================================================
-- USUARIOS (roles: admin, mecanico, logistica, conductor, observador)
-- =====================================================
CREATE TABLE usuario (
    id_usuario INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL,
    correo VARCHAR(50) UNIQUE COLLATE utf8mb4_unicode_ci NOT NULL,
    password VARCHAR(128) NOT NULL,
    rol ENUM('admin','mecanico','logistica','conductor','observador') NOT NULL
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO usuario (id_usuario, nombre, correo, password, rol) VALUES
(1,'Admin Principal','admin@correo.com','admin123','admin'),
(2,'Mecánico Juan','mecanico@correo.com','mecanico123','mecanico'),
(3,'Pedro Ramírez','conductor@correo.com','conductor123','conductor'),
(4,'Carlos López','logistica@correo.com','logistica123','logistica'),
(5,'Laura Martínez','observador@correo.com','observador123','observador');

-- =====================================================
-- CONDUCTOR
-- =====================================================
CREATE TABLE conductor (
    id_conductor INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(60) NOT NULL COLLATE utf8mb4_unicode_ci,
    apellido VARCHAR(60) NOT NULL COLLATE utf8mb4_unicode_ci,
    telefono VARCHAR(20) COLLATE utf8mb4_unicode_ci,
    direccion VARCHAR(100) COLLATE utf8mb4_unicode_ci,
    fecha_nacimiento DATE,
    id_usuario INT NULL,
    CONSTRAINT fk_conductor_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE SET NULL
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO conductor (id_conductor, nombre, apellido, telefono, direccion, fecha_nacimiento, id_usuario) VALUES
(1,'Pedro','Ramírez','5555121234','Calle Uno 123, CDMX','1980-06-10',3),  -- vinculado al usuario conductor
(2,'María','Sosa','5556232345','Calle Dos 456, Puebla','1985-12-15',NULL),
(3,'Carlos','Gómez','5557343456','Calle Tres 789, Querétaro','1982-03-22',NULL),
(4,'Ana','Torres','5558454567','Calle Cuatro 101, Guadalajara','1988-07-30',NULL),
(5,'Luis','Fernández','5559565678','Calle Cinco 202, Monterrey','1979-11-05',NULL),
(6,'Laura','Díaz','5550676789','Calle Seis 303, Veracruz','1990-01-14',NULL),
(7,'José','Martínez','5551787890','Calle Siete 404, León','1984-09-20',NULL),
(8,'Marta','Sánchez','5552898901','Calle Ocho 505, Cancún','1987-04-11',NULL),
(9,'Andrés','Hernández','5553909012','Calle Nueve 606, Acapulco','1983-10-25',NULL),
(10,'Lucía','Mendoza','5554010123','Calle Diez 707, Tijuana','1991-02-08',NULL),
(11,'Francisco','López','5555129999','Calle Once 808, SLP','1981-05-17',NULL),
(12,'Isabella','García','5556230000','Calle Doce 909, Toluca','1989-08-03',NULL);

-- =====================================================
-- VEHÍCULO (estado cubre: 'activo','mantenimiento','inactivo')
-- =====================================================
CREATE TABLE vehiculo (
    id_vehiculo INT PRIMARY KEY AUTO_INCREMENT,
    matricula VARCHAR(20) UNIQUE NOT NULL COLLATE utf8mb4_unicode_ci,
    modelo VARCHAR(50) NOT NULL COLLATE utf8mb4_unicode_ci,
    tipo VARCHAR(30) NOT NULL COLLATE utf8mb4_unicode_ci,
    capacidad INT NOT NULL,
    marca VARCHAR(30) NOT NULL COLLATE utf8mb4_unicode_ci,
    estado ENUM('activo','mantenimiento','inactivo') NOT NULL DEFAULT 'activo',
    kilometraje INT NOT NULL,
    id_flota INT NULL,
    id_conductor INT NULL,
    CONSTRAINT fk_vehiculo_flota FOREIGN KEY (id_flota) REFERENCES flota(id_flota) ON DELETE SET NULL,
    CONSTRAINT fk_vehiculo_conductor FOREIGN KEY (id_conductor) REFERENCES conductor(id_conductor) ON DELETE SET NULL
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO vehiculo (id_vehiculo, matricula, modelo, tipo, capacidad, marca, estado, kilometraje, id_flota, id_conductor) VALUES
(1,'ABC123','Sprinter 2020','Camioneta',1000,'Mercedes-Benz','activo',25000,3,1),
(2,'XYZ789','Transit 2018','Furgoneta',800,'Ford','mantenimiento',74000,3,2),
(3,'DEF456','Hilux 2022','Camioneta',1200,'Toyota','activo',15000,1,3),
(4,'GHI789','Freightliner 2021','Camión',5000,'Freightliner','activo',50000,4,4),
(5,'JKL012','Versa 2023','Sedán',500,'Nissan','activo',8000,2,5),
(6,'MNO345','Kenworth 2020','Camión',4500,'Kenworth','inactivo',120000,4,6),
(7,'PQR678','RAV4 2021','SUV',700,'Toyota','activo',35000,1,7),
(8,'STU901','Volvo 2019','Camión',5500,'Volvo','activo',95000,4,8),
-- CORRECCIÓN: id_flota antes era 9 (no existe) -> cambiado a 2
(9,'VWX234','Aveo 2022','Sedán',450,'Chevrolet','activo',12000,2,9),
(10,'YZA567','CX-5 2020','SUV',650,'Mazda','mantenimiento',42000,1,10),
(11,'BCD890','Doblado 2019','Furgoneta',750,'Hyundai','activo',88000,3,11),
(12,'EFG123','Tacoma 2021','Camioneta',950,'Toyota','activo',22000,1,12),
(13,'HIJ456','F-150 2020','Camioneta',1100,'Ford','activo',60000,1,NULL),
(14,'KLM789','Fortuner 2022','SUV',800,'Toyota','activo',18000,1,NULL),
(15,'NOP012','Ranger 2021','Camioneta',900,'Ford','inactivo',45000,1,NULL);

-- =====================================================
-- ORDEN DE SERVICIO (estado: pendiente, en progreso, completado, cancelado)
-- =====================================================
CREATE TABLE orden_servicio (
    id_orden INT PRIMARY KEY AUTO_INCREMENT,
    descripcion VARCHAR(255) COLLATE utf8mb4_unicode_ci,
    fecha DATE,
    estado ENUM('pendiente','en progreso','completado','cancelado') NOT NULL DEFAULT 'pendiente'
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO orden_servicio (id_orden, descripcion, fecha, estado) VALUES
(1,'Paquete refrigerado','2024-06-01','completado'),
(2,'Material industrial','2024-06-02','en progreso'),
(3,'Entrega de documentos','2024-06-03','completado'),
(4,'Carga de mercancía','2024-06-04','pendiente'),
(5,'Mudanza residencial','2024-06-05','cancelado'),
(6,'Transporte de valores','2024-06-06','completado'),
(7,'Envío de repuestos','2024-06-07','en progreso'),
(8,'Carga de construcción','2024-06-08','pendiente'),
(9,'Entrega urgente','2024-06-09','pendiente'),
(10,'Reparto local','2024-06-10','completado'),
(11,'Traslado internacional','2024-06-11','en progreso'),
(12,'Servicio especial','2024-06-12','pendiente'),
(13,'Ruta express','2024-06-13','completado'),
(14,'Carga pesada','2024-06-14','en progreso'),
(15,'Entrega programada','2024-06-15','pendiente');

-- =====================================================
-- VIAJE (incluye fecha_estimada y estados: pendiente, en progreso, completado, cancelado)
-- =====================================================
CREATE TABLE viaje (
    id_viaje INT PRIMARY KEY AUTO_INCREMENT,
    origen VARCHAR(50) COLLATE utf8mb4_unicode_ci,
    destino VARCHAR(50) COLLATE utf8mb4_unicode_ci,
    fecha_salida DATE,
    fecha_estimada DATE NULL,
    estado ENUM('pendiente','en progreso','completado','cancelado') NOT NULL DEFAULT 'pendiente',
    id_vehiculo INT NULL,
    id_conductor INT NULL,
    id_orden INT NULL,
    CONSTRAINT fk_viaje_vehiculo FOREIGN KEY (id_vehiculo) REFERENCES vehiculo(id_vehiculo) ON DELETE SET NULL,
    CONSTRAINT fk_viaje_conductor FOREIGN KEY (id_conductor) REFERENCES conductor(id_conductor) ON DELETE SET NULL,
    CONSTRAINT fk_viaje_orden FOREIGN KEY (id_orden) REFERENCES orden_servicio(id_orden) ON DELETE SET NULL
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO viaje (id_viaje, origen, destino, fecha_salida, fecha_estimada, estado, id_vehiculo, id_conductor, id_orden) VALUES
(1,'CDMX','Puebla','2024-06-01','2024-06-01','completado',1,1,1),
(2,'Querétaro','León','2024-06-02','2024-06-03','en progreso',2,2,2),
(3,'CDMX','Guadalajara','2024-06-03','2024-06-05','completado',3,3,3),
(4,'Monterrey','CDMX','2024-06-04',NULL,'completado',4,4,4),
(5,'CDMX','Veracruz','2024-06-05','2024-06-06','en progreso',5,5,5),
(6,'Cancún','Playa del Carmen','2024-06-06','2024-06-07','completado',6,6,6),
(7,'CDMX','Toluca','2024-06-07','2024-06-09','completado',7,7,7),
(8,'Tijuana','CDMX','2024-06-08',NULL,'pendiente',8,8,8),
(9,'CDMX','Acapulco','2024-06-09','2024-06-10','en progreso',9,9,9),
(10,'San Luis Potosí','CDMX','2024-06-10',NULL,'completado',10,10,10),
(11,'CDMX','Mérida','2024-06-11','2024-06-13','completado',1,11,11),
(12,'Guadalajara','Monterrey','2024-06-12','2024-06-15','en progreso',2,12,12),
(13,'CDMX','Cuernavaca','2024-06-13','2024-06-14','completado',3,1,13),
(14,'León','Querétaro','2024-06-14','2024-06-16','en progreso',4,2,14),
(15,'CDMX','Taxco','2024-06-15','2024-06-18','completado',5,3,15);

-- =====================================================
-- MANTENIMIENTO (tipo: preventivo, correctivo, reparacion)
-- =====================================================
CREATE TABLE mantenimiento (
    id_mantenimiento INT PRIMARY KEY AUTO_INCREMENT,
    id_vehiculo INT NOT NULL,
    tipo ENUM('preventivo','correctivo','reparacion') COLLATE utf8mb4_unicode_ci NOT NULL,
    descripcion VARCHAR(255) COLLATE utf8mb4_unicode_ci NOT NULL,
    costo DECIMAL(10,2) NOT NULL,
    fecha DATE NOT NULL,
    FOREIGN KEY (id_vehiculo) REFERENCES vehiculo(id_vehiculo) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO mantenimiento (id_mantenimiento, id_vehiculo, tipo, descripcion, costo, fecha) VALUES
(1,1,'preventivo','Cambio de aceite y filtro',850.00,'2024-05-20'),
(2,2,'reparacion','Reparación de frenos',2800.00,'2024-05-30'),
(3,3,'reparacion','Revisión de suspensión y cambio de bujes',4200.00,'2024-06-01'),
(4,4,'correctivo','Cambio de llanta trasera',1800.00,'2024-06-05'),
(5,5,'correctivo','Reparación de transmisión',9500.00,'2024-06-10'),
(6,6,'preventivo','Servicio general',1200.00,'2024-06-12'),
(7,10,'preventivo','Revisión preventiva (ejemplo)',600.00,'2024-06-18');

-- =====================================================
-- CONSUMO (tipo_combustible ejemplos: Gasolina, Diésel, Eléctrico, Gas)
-- =====================================================
CREATE TABLE consumo (
    id_consumo INT PRIMARY KEY AUTO_INCREMENT,
    matricula VARCHAR(20) COLLATE utf8mb4_unicode_ci,
    litros DECIMAL(10,2),
    fecha DATE,
    tipo_combustible VARCHAR(30) COLLATE utf8mb4_unicode_ci,
    costo DECIMAL(10,2),
    FOREIGN KEY (matricula) REFERENCES vehiculo(matricula) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO consumo (id_consumo, matricula, litros, fecha, tipo_combustible, costo) VALUES
(1,'ABC123',60.00,'2024-06-01','Gasolina',1200.00),
(2,'XYZ789',55.50,'2024-06-02','Diésel',1100.00),
(3,'DEF456',48.00,'2024-06-03','Gasolina',980.00),
(4,'GHI789',120.50,'2024-06-04','Diésel',2600.00),
(5,'JKL012',35.00,'2024-06-05','Gasolina',700.00),
(6,'MNO345',110.00,'2024-06-06','Diésel',2350.00),
(7,'PQR678',52.50,'2024-06-07','Gasolina',1050.00),
(8,'STU901',115.00,'2024-06-08','Diésel',2450.00),
(9,'VWX234',40.00,'2024-06-09','Gasolina',820.00),
(10,'YZA567',58.00,'2024-06-10','Gasolina',1180.00),
(11,'ABC123',62.50,'2024-06-11','Gasolina',1250.00),
(12,'DEF456',50.00,'2024-06-12','Eléctrico',0.00),
(13,'JKL012',38.50,'2024-06-13','Gas',770.00),
(14,'PQR678',55.00,'2024-06-14','Gasolina',1100.00),
(15,'VWX234',42.00,'2024-06-15','Gasolina',860.00);

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

INSERT INTO incidente (id_incidente, matricula, tipo, fecha, descripcion) VALUES
(1,'ABC123','accidente','2024-06-01','Pequeño choque en caseta'),
(2,'XYZ789','infracción','2024-06-02','Exceso de velocidad detectado'),
(3,'DEF456','daño','2024-06-03','Espejo lateral roto');

-- =====================================================
-- LICENCIA
-- =====================================================
CREATE TABLE licencia (
    id_licencia INT PRIMARY KEY AUTO_INCREMENT,
    id_conductor INT NOT NULL,
    tipo ENUM('A','A1','A2','B','B1','C','D','E','F','G','H','AM') COLLATE utf8mb4_unicode_ci NOT NULL,
    fecha_emision DATE NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    FOREIGN KEY (id_conductor) REFERENCES conductor(id_conductor) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO licencia (id_licencia, id_conductor, tipo, fecha_emision, fecha_vencimiento) VALUES
(1,1,'A','2020-01-01','2025-01-01'),
(2,1,'B','2022-06-01','2027-06-01'),
(3,2,'A','2019-03-15','2024-03-15'),
(4,3,'C','2021-09-10','2026-09-10');

-- =====================================================
-- EVALUACION (puntuacion ejemplo 1..10)
-- =====================================================
CREATE TABLE evaluacion (
    id_evaluacion INT PRIMARY KEY AUTO_INCREMENT,
    id_conductor INT NOT NULL,
    fecha DATE NOT NULL,
    puntuacion INT NOT NULL,
    comentarios VARCHAR(255) COLLATE utf8mb4_unicode_ci,
    FOREIGN KEY (id_conductor) REFERENCES conductor(id_conductor) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO evaluacion (id_evaluacion, id_conductor, fecha, puntuacion, comentarios) VALUES
(1,1,'2024-05-10',9,'Conductor puntual y cuidadoso con el vehículo'),
(2,2,'2024-05-12',8,'Buen rendimiento en revisiones'),
(3,3,'2024-05-15',9,'Cumple rutas asignadas de forma eficiente');

-- =====================================================
-- FIN - índices útiles
-- =====================================================
ALTER TABLE viaje ADD INDEX (fecha_salida);
ALTER TABLE mantenimiento ADD INDEX (fecha);
ALTER TABLE consumo ADD INDEX (fecha);