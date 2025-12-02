-- Configuración de codificación para soportar caracteres internacionales
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET COLLATION_CONNECTION=utf8mb4_unicode_ci;

-- Reinicia la base de datos (solo para entornos de desarrollo)
DROP DATABASE IF EXISTS flota_logistica;
CREATE DATABASE flota_logistica CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE flota_logistica;

-- =====================================================
-- FLOTA (mejorada con categoría, ubicación, políticas y estado)
-- =====================================================
-- Tabla principal de flotas
CREATE TABLE flota (
    id_flota INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(40) COLLATE utf8mb4_unicode_ci NOT NULL,
    descripcion VARCHAR(100) COLLATE utf8mb4_unicode_ci,
    categoria ENUM('carga_ligera','carga_pesada','transporte_personal','reparto','especial') NOT NULL DEFAULT 'carga_ligera',
    ubicacion VARCHAR(100) COLLATE utf8mb4_unicode_ci NOT NULL,
    estado ENUM('activa','inactiva','mantenimiento') NOT NULL DEFAULT 'activa',
    politica_uso TEXT COLLATE utf8mb4_unicode_ci,
    capacidad_maxima INT DEFAULT 0,
    fecha_creacion DATE NOT NULL
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Datos de ejemplo iniciales para flotas
INSERT INTO flota (id_flota, nombre, descripcion, categoria, ubicacion, estado, politica_uso, capacidad_maxima, fecha_creacion) VALUES
(1,'Flota Norte','Vehículos de la zona Norte','carga_ligera','Ciudad de México - Zona Norte','activa','Uso exclusivo para entregas locales en zona norte. Máximo 8 horas diarias. Requiere autorización para salidas nocturnas.',10,'2024-01-15'),
(2,'Flota Sur','Vehículos de la zona Sur','reparto','Ciudad de México - Zona Sur','activa','Reparto urbano. Horario: 7:00-19:00. Prohibido circular en contingencias ambientales.',8,'2024-01-20'),
(3,'Flota Centro','Vehículos de la zona Centro','transporte_personal','Ciudad de México - Centro','activa','Transporte ejecutivo y documentos. Requiere conductor con licencia tipo B. Mantenimiento preventivo cada 5000 km.',5,'2024-02-01'),
(4,'Flota Especial','Vehículos para carga pesada','carga_pesada','Nacional - Rutas Largas','activa','Carga pesada nacional. Conductores con mínimo 5 años experiencia. Descanso obligatorio cada 4 horas. GPS requerido.',15,'2024-01-10');

-- =====================================================
-- USUARIOS (roles: admin, mecanico, logistica, conductor, observador)
-- =====================================================
-- Tabla de usuarios del sistema (roles y autenticación básica)
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
-- Tabla de conductores
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
-- Tabla de vehículos (incluye categoría para alinearse con flota)
CREATE TABLE vehiculo (
    id_vehiculo INT PRIMARY KEY AUTO_INCREMENT,
    matricula VARCHAR(20) UNIQUE NOT NULL COLLATE utf8mb4_unicode_ci,
    modelo VARCHAR(50) NOT NULL COLLATE utf8mb4_unicode_ci,
    tipo VARCHAR(30) NOT NULL COLLATE utf8mb4_unicode_ci,
    capacidad INT NOT NULL,
    marca VARCHAR(30) NOT NULL COLLATE utf8mb4_unicode_ci,
    estado ENUM('activo','mantenimiento','inactivo') NOT NULL DEFAULT 'activo',
    kilometraje INT NOT NULL,
    categoria ENUM('carga_ligera','carga_pesada','transporte_personal','reparto','especial') NOT NULL DEFAULT 'carga_ligera',
    id_flota INT NULL,
    id_conductor INT NULL,
    CONSTRAINT fk_vehiculo_flota FOREIGN KEY (id_flota) REFERENCES flota(id_flota) ON DELETE SET NULL,
    CONSTRAINT fk_vehiculo_conductor FOREIGN KEY (id_conductor) REFERENCES conductor(id_conductor) ON DELETE SET NULL
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO vehiculo (id_vehiculo, matricula, modelo, tipo, capacidad, marca, estado, kilometraje, categoria, id_flota, id_conductor) VALUES
(1,'ABC123','Sprinter 2020','Camioneta',1000,'Mercedes-Benz','activo',25000,'transporte_personal',3,1),
(2,'XYZ789','Transit 2018','Furgoneta',800,'Ford','mantenimiento',74000,'transporte_personal',3,2),
(3,'DEF456','Hilux 2022','Camioneta',1200,'Toyota','activo',15000,'carga_ligera',1,3),
(4,'GHI789','Freightliner 2021','Camión',5000,'Freightliner','activo',50000,'carga_pesada',4,4),
(5,'JKL012','Versa 2023','Sedán',500,'Nissan','activo',8000,'reparto',2,5),
(6,'MNO345','Kenworth 2020','Camión',4500,'Kenworth','inactivo',120000,'carga_pesada',4,6),
(7,'PQR678','RAV4 2021','SUV',700,'Toyota','activo',35000,'carga_ligera',1,7),
(8,'STU901','Volvo 2019','Camión',5500,'Volvo','activo',95000,'carga_pesada',4,8),
(9,'VWX234','Aveo 2022','Sedán',450,'Chevrolet','activo',12000,'reparto',2,9),
(10,'YZA567','CX-5 2020','SUV',650,'Mazda','mantenimiento',42000,'carga_ligera',1,10),
(11,'BCD890','Doblado 2019','Furgoneta',750,'Hyundai','activo',88000,'transporte_personal',3,11),
(12,'EFG123','Tacoma 2021','Camioneta',950,'Toyota','activo',22000,'carga_ligera',1,12),
(13,'HIJ456','F-150 2020','Camioneta',1100,'Ford','activo',60000,'carga_ligera',1,NULL),
(14,'KLM789','Fortuner 2022','SUV',800,'Toyota','activo',18000,'carga_ligera',1,NULL),
(15,'NOP012','Ranger 2021','Camioneta',900,'Ford','inactivo',45000,'carga_ligera',1,NULL);

-- =====================================================
-- ORDEN DE SERVICIO (estado: pendiente, en progreso, completado, cancelado)
-- =====================================================
-- Tabla de órdenes de servicio
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
-- Tabla de viajes (incluye estado y referencia a vehículo/conductor/orden)
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
-- Tabla de mantenimiento de vehículos
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
-- Tabla de consumo de combustible por matrícula de vehículo
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
-- Tabla de incidentes asociados a un vehículo
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
-- Tabla de licencias de conductores
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
-- Tabla de evaluaciones de desempeño de conductores
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
-- FLOTA_VEHICULO (tabla intermedia para asignaciones específicas)
-- NOTA: Se crea al final porque depende de flota y vehiculo
-- =====================================================
-- Tabla de asignaciones de vehículos a flotas (intermedia)
CREATE TABLE flota_vehiculo (
    id_asignacion INT PRIMARY KEY AUTO_INCREMENT,
    id_flota INT NOT NULL,
    id_vehiculo INT NOT NULL,
    fecha_asignacion DATE NOT NULL,
    fecha_desasignacion DATE NULL,
    motivo_asignacion VARCHAR(255) COLLATE utf8mb4_unicode_ci,
    estado_asignacion ENUM('activa','finalizada','temporal') NOT NULL DEFAULT 'activa',
    prioridad ENUM('baja','media','alta','critica') NOT NULL DEFAULT 'media',
    notas TEXT COLLATE utf8mb4_unicode_ci,
    FOREIGN KEY (id_flota) REFERENCES flota(id_flota) ON DELETE CASCADE,
    FOREIGN KEY (id_vehiculo) REFERENCES vehiculo(id_vehiculo) ON DELETE CASCADE,
    UNIQUE KEY uk_flota_vehiculo_activa (id_vehiculo, id_flota, estado_asignacion)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO flota_vehiculo (id_asignacion, id_flota, id_vehiculo, fecha_asignacion, fecha_desasignacion, motivo_asignacion, estado_asignacion, prioridad, notas) VALUES
(1,3,1,'2024-03-01',NULL,'Asignación inicial para reparto zona centro','activa','alta','Vehículo nuevo, requiere seguimiento'),
(2,3,2,'2024-03-05',NULL,'Soporte adicional zona centro','activa','media','En mantenimiento preventivo'),
(3,1,3,'2024-02-15',NULL,'Entregas zona norte','activa','alta','Rendimiento óptimo'),
(4,4,4,'2024-01-20',NULL,'Rutas largas nacionales','activa','critica','Conductor exclusivo asignado'),
(5,2,5,'2024-03-10',NULL,'Reparto urbano sur','activa','baja','Vehículo económico'),
(6,4,6,'2024-02-01','2024-06-15','Ruta temporal','finalizada','media','Desasignado por mantenimiento mayor'),
(7,1,7,'2024-03-15',NULL,'Apoyo zona norte','activa','media','SUV para cargas especiales'),
(8,4,8,'2024-02-20',NULL,'Carga pesada','activa','critica','Camión principal flota pesada'),
(9,2,9,'2024-03-20',NULL,'Reparto rápido','activa','alta','Para entregas urgentes'),
(10,1,10,'2024-03-01',NULL,'Zona norte - SUV','activa','media','En mantenimiento'),
(11,3,11,'2024-02-25',NULL,'Centro - furgoneta','activa','media','Buen estado general'),
(12,1,12,'2024-03-05',NULL,'Norte - camioneta','activa','alta','Recién incorporado');

-- =====================================================
-- TABLA DE LOGS (auditoría de operaciones)
-- =====================================================
-- Tabla de auditoría: registra acciones de crear/modificar/eliminar
CREATE TABLE logs (
    id_log INT PRIMARY KEY AUTO_INCREMENT,
    id_usuario INT NULL,
    usuario_nombre VARCHAR(100) COLLATE utf8mb4_unicode_ci,
    accion ENUM('crear','modificar','eliminar') NOT NULL,
    tabla VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL,
    registro_id INT NULL,
    detalle TEXT COLLATE utf8mb4_unicode_ci,
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE SET NULL
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- =====================================================
-- FIN - índices útiles
-- =====================================================
-- Índices útiles para mejorar rendimiento en consultas por fecha
ALTER TABLE viaje ADD INDEX (fecha_salida);
ALTER TABLE mantenimiento ADD INDEX (fecha);
ALTER TABLE consumo ADD INDEX (fecha);
ALTER TABLE logs ADD INDEX (fecha_hora);
ALTER TABLE logs ADD INDEX (tabla);

-- =====================================================
-- INSERCIÓN MASIVA DE 1000 REGISTROS POR TABLA
-- Propósito: poblar las tablas con datos realistas para pruebas y análisis.
-- Metodología: procedimientos almacenados con pools de valores coherentes (nombres, ciudades, modelos, etc.).
-- Nota: Se empleó ayuda de IA exclusivamente para esta sección de generación masiva.
-- =====================================================

-- PARTE HECHA CON IA PARA GENERAR DATOS DE PRUEBA ADICIONALES

-- Generar 1000 flotas adicionales
DELIMITER //
-- Procedimiento: genera flotas con categorías, ubicaciones y políticas de uso
CREATE PROCEDURE generar_flotas()
BEGIN
    DECLARE i INT DEFAULT 5;
    DECLARE categorias VARCHAR(255) DEFAULT 'carga_ligera,carga_pesada,transporte_personal,reparto,especial';
    DECLARE estados VARCHAR(255) DEFAULT 'activa,inactiva,mantenimiento';
    DECLARE cat VARCHAR(50);
    DECLARE est VARCHAR(50);
    DECLARE ciudad VARCHAR(50);
    DECLARE nombres_flota VARCHAR(255) DEFAULT 'Norte,Sur,Centro,Pacífico,Bajío,Altiplano,Occidente,Oriente,Metropolitana,Regional';
    DECLARE ubicaciones VARCHAR(255) DEFAULT 'Ciudad de México,Guadalajara,Monterrey,Puebla,Tijuana,Mérida,León,Querétaro,Chihuahua,Saltillo';
    
    WHILE i <= 1000 DO
        SET cat = ELT(FLOOR(1 + RAND() * 5), 'carga_ligera','carga_pesada','transporte_personal','reparto','especial');
        SET est = ELT(FLOOR(1 + RAND() * 3), 'activa','inactiva','mantenimiento');
        SET ciudad = ELT(FLOOR(1 + RAND() * 10), 'Ciudad de México','Guadalajara','Monterrey','Puebla','Tijuana','Mérida','León','Querétaro','Chihuahua','Saltillo');
        
        INSERT INTO flota (nombre, descripcion, categoria, ubicacion, estado, politica_uso, capacidad_maxima, fecha_creacion)
        VALUES (
            CONCAT('Flota ', ELT(FLOOR(1 + RAND() * 10), 'Norte','Sur','Centro','Pacífico','Bajío','Altiplano','Occidente','Oriente','Metropolitana','Regional')),
            CONCAT('Operaciones en ', ciudad, ' con enfoque en ', cat),
            cat,
            ciudad,
            est,
            CONCAT('Uso según normativa local, descanso obligatorio, mantenimiento preventivo cada ', ELT(FLOOR(1 + RAND() * 4), '5000','8000','10000','12000'), ' km.'),
            FLOOR(5 + RAND() * 50),
            DATE_ADD('2024-01-01', INTERVAL FLOOR(RAND() * 365) DAY)
        );
        SET i = i + 1;
    END WHILE;
END//
DELIMITER ;

-- Generar 1000 usuarios adicionales
DELIMITER //
-- Procedimiento: genera usuarios con nombres y correos únicos
CREATE PROCEDURE generar_usuarios()
BEGIN
    DECLARE i INT DEFAULT 6;
    DECLARE roles VARCHAR(255) DEFAULT 'admin,mecanico,logistica,conductor,observador';
    DECLARE rol VARCHAR(20);
    DECLARE nombres VARCHAR(255) DEFAULT 'Juan,Carlos,Ana,María,Luis,Laura,José,Lucía,Pedro,Valeria,Raúl,Elena,Andrés,Isabel,Diego';
    DECLARE apellidos VARCHAR(255) DEFAULT 'López,García,Ramírez,Hernández,Martínez,Rodríguez,González,Pérez,Sánchez,Fernández,Romero,Silva,Castro,Vargas,Núñez';
    
    WHILE i <= 1000 DO
        SET rol = ELT(FLOOR(1 + RAND() * 5), 'admin','mecanico','logistica','conductor','observador');
        
        INSERT INTO usuario (nombre, correo, password, rol)
        VALUES (
            CONCAT(ELT(FLOOR(1 + RAND() * 15), 'Juan','Carlos','Ana','María','Luis','Laura','José','Lucía','Pedro','Valeria','Raúl','Elena','Andrés','Isabel','Diego'), ' ', ELT(FLOOR(1 + RAND() * 15), 'López','García','Ramírez','Hernández','Martínez','Rodríguez','González','Pérez','Sánchez','Fernández','Romero','Silva','Castro','Vargas','Núñez')),
            CONCAT(
                LOWER(REPLACE(ELT(FLOOR(1 + RAND() * 15), 'Juan','Carlos','Ana','María','Luis','Laura','José','Lucía','Pedro','Valeria','Raúl','Elena','Andrés','Isabel','Diego'), 'á','a')),
                '.',
                LOWER(REPLACE(ELT(FLOOR(1 + RAND() * 15), 'López','García','Ramírez','Hernández','Martínez','Rodríguez','González','Pérez','Sánchez','Fernández','Romero','Silva','Castro','Vargas','Núñez'), 'á','a')),
                '.', i,
                '@empresa.com'
            ),
            CONCAT('pw', LPAD(FLOOR(RAND()*100000),5,'0')),
            rol
        );
        SET i = i + 1;
    END WHILE;
END//
DELIMITER ;

-- Generar 1000 conductores adicionales
DELIMITER //
-- Procedimiento: genera conductores con datos personales verosímiles
CREATE PROCEDURE generar_conductores()
BEGIN
    DECLARE i INT DEFAULT 13;
    DECLARE user_id INT;
    DECLARE nombres VARCHAR(255) DEFAULT 'Juan,Carlos,Ana,María,Luis,Laura,José,Lucía,Pedro,Valeria,Raúl,Elena,Andrés,Isabel,Diego';
    DECLARE apellidos VARCHAR(255) DEFAULT 'López,García,Ramírez,Hernández,Martínez,Rodríguez,González,Pérez,Sánchez,Fernández,Romero,Silva,Castro,Vargas,Núñez';
    DECLARE calles VARCHAR(255) DEFAULT 'Primera,Segunda,Tercera,Cuarta,Quinta,Sexta,Séptima,Octava,Novena,Décima';
    DECLARE ciudades VARCHAR(255) DEFAULT 'CDMX,Guadalajara,Monterrey,Puebla,Tijuana,Mérida,León,Querétaro,Chihuahua,Saltillo';
    
    WHILE i <= 1000 DO
        SET user_id = IF(RAND() > 0.5 AND i <= 1000, FLOOR(6 + RAND() * 995), NULL);
        
        INSERT INTO conductor (nombre, apellido, telefono, direccion, fecha_nacimiento, id_usuario)
        VALUES (
            ELT(FLOOR(1 + RAND() * 15), 'Juan','Carlos','Ana','María','Luis','Laura','José','Lucía','Pedro','Valeria','Raúl','Elena','Andrés','Isabel','Diego'),
            ELT(FLOOR(1 + RAND() * 15), 'López','García','Ramírez','Hernández','Martínez','Rodríguez','González','Pérez','Sánchez','Fernández','Romero','Silva','Castro','Vargas','Núñez'),
            CONCAT('55', LPAD(FLOOR(RAND()*9000000)+1000000, 7, '0')),
            CONCAT('Calle ', ELT(FLOOR(1 + RAND() * 10), 'Primera','Segunda','Tercera','Cuarta','Quinta','Sexta','Séptima','Octava','Novena','Décima'), ' #', FLOOR(1 + RAND() * 999), ', ', ELT(FLOOR(1 + RAND() * 10), 'CDMX','Guadalajara','Monterrey','Puebla','Tijuana','Mérida','León','Querétaro','Chihuahua','Saltillo')),
            DATE_ADD('1970-01-01', INTERVAL FLOOR(RAND() * 18250) DAY),
            user_id
        );
        SET i = i + 1;
    END WHILE;
END//
DELIMITER ;

-- Generar 1000 vehículos adicionales
DELIMITER //
-- Procedimiento: genera vehículos con marcas/modelos reales
CREATE PROCEDURE generar_vehiculos()
BEGIN
    DECLARE i INT DEFAULT 16;
    DECLARE estados VARCHAR(255) DEFAULT 'activo,mantenimiento,inactivo';
    DECLARE categorias VARCHAR(255) DEFAULT 'carga_ligera,carga_pesada,transporte_personal,reparto,especial';
    DECLARE est VARCHAR(20);
    DECLARE cat VARCHAR(50);
    DECLARE flota_id INT;
    DECLARE cond_id INT;
    DECLARE tipos VARCHAR(255) DEFAULT 'Camioneta,Furgoneta,Camión,Sedán,SUV';
    DECLARE marcas VARCHAR(255) DEFAULT 'Toyota,Ford,Chevrolet,Nissan,Volkswagen,Mercedes-Benz,Volvo,Freightliner,Kenworth,Hyundai,Mazda,Honda,Renault,Peugeot,Scania';
    DECLARE modelos VARCHAR(255) DEFAULT 'Hilux,F-150,Sprinter,Transit,Ranger,Tacoma,Versa,Aveo,CX-5,RAV4,Fortuner,Onix,Sandero,Logan,Actros';
    
    WHILE i <= 1000 DO
        SET est = ELT(FLOOR(1 + RAND() * 3), 'activo','mantenimiento','inactivo');
        SET cat = ELT(FLOOR(1 + RAND() * 5), 'carga_ligera','carga_pesada','transporte_personal','reparto','especial');
        SET flota_id = IF(RAND() > 0.1, FLOOR(1 + RAND() * 1000), NULL);
        SET cond_id = IF(RAND() > 0.3, FLOOR(1 + RAND() * 1000), NULL);
        
        INSERT INTO vehiculo (matricula, modelo, tipo, capacidad, marca, estado, kilometraje, categoria, id_flota, id_conductor)
        VALUES (
            CONCAT('VEH', LPAD(i, 6, '0')),
            ELT(FLOOR(1 + RAND() * 15), 'Hilux','F-150','Sprinter','Transit','Ranger','Tacoma','Versa','Aveo','CX-5','RAV4','Fortuner','Onix','Sandero','Logan','Actros'),
            ELT(FLOOR(1 + RAND() * 5), 'Camioneta','Furgoneta','Camión','Sedán','SUV'),
            FLOOR(400 + RAND() * 5000),
            ELT(FLOOR(1 + RAND() * 15), 'Toyota','Ford','Chevrolet','Nissan','Volkswagen','Mercedes-Benz','Volvo','Freightliner','Kenworth','Hyundai','Mazda','Honda','Renault','Peugeot','Scania'),
            est,
            FLOOR(1000 + RAND() * 150000),
            cat,
            flota_id,
            cond_id
        );
        SET i = i + 1;
    END WHILE;
END//
DELIMITER ;

-- Generar 1000 órdenes de servicio adicionales
DELIMITER //
-- Procedimiento: genera órdenes de servicio con descripciones comunes
CREATE PROCEDURE generar_ordenes()
BEGIN
    DECLARE i INT DEFAULT 16;
    DECLARE est VARCHAR(20);
    DECLARE descrip VARCHAR(255);
    
    WHILE i <= 1000 DO
        SET est = ELT(FLOOR(1 + RAND() * 4), 'pendiente','en progreso','completado','cancelado');
        SET descrip = ELT(FLOOR(1 + RAND() * 12),
            'Entrega refrigerada', 'Transporte de materiales', 'Documentos urgentes', 'Carga de mercancía',
            'Mudanza residencial', 'Transporte de valores', 'Envío de repuestos', 'Construcción',
            'Reparto local', 'Traslado internacional', 'Servicio especial', 'Ruta express'
        );
        
        INSERT INTO orden_servicio (descripcion, fecha, estado)
        VALUES (
            descrip,
            DATE_ADD('2024-01-01', INTERVAL FLOOR(RAND() * 365) DAY),
            est
        );
        SET i = i + 1;
    END WHILE;
END//
DELIMITER ;

-- Generar 1000 viajes adicionales
DELIMITER //
-- Procedimiento: genera viajes entre ciudades comunes en México
CREATE PROCEDURE generar_viajes()
BEGIN
    DECLARE i INT DEFAULT 16;
    DECLARE est VARCHAR(20);
    DECLARE fecha_s DATE;
    DECLARE fecha_e DATE;
    DECLARE origen_c VARCHAR(50);
    DECLARE destino_c VARCHAR(50);
    
    WHILE i <= 1000 DO
        SET est = ELT(FLOOR(1 + RAND() * 4), 'pendiente','en progreso','completado','cancelado');
        SET fecha_s = DATE_ADD('2024-01-01', INTERVAL FLOOR(RAND() * 365) DAY);
        SET fecha_e = IF(RAND() > 0.2, DATE_ADD(fecha_s, INTERVAL FLOOR(1 + RAND() * 10) DAY), NULL);
        SET origen_c = ELT(FLOOR(1 + RAND() * 10), 'CDMX','Guadalajara','Monterrey','Puebla','Tijuana','Mérida','León','Querétaro','Chihuahua','Saltillo');
        SET destino_c = ELT(FLOOR(1 + RAND() * 10), 'CDMX','Guadalajara','Monterrey','Puebla','Tijuana','Mérida','León','Querétaro','Chihuahua','Saltillo');
        
        INSERT INTO viaje (origen, destino, fecha_salida, fecha_estimada, estado, id_vehiculo, id_conductor, id_orden)
        VALUES (
            origen_c,
            destino_c,
            fecha_s,
            fecha_e,
            est,
            FLOOR(1 + RAND() * 1000),
            FLOOR(1 + RAND() * 1000),
            IF(RAND() > 0.1, FLOOR(1 + RAND() * 1000), NULL)
        );
        SET i = i + 1;
    END WHILE;
END//
DELIMITER ;

-- Generar 1000 mantenimientos adicionales
DELIMITER //
-- Procedimiento: genera mantenimientos típicos
CREATE PROCEDURE generar_mantenimientos()
BEGIN
    DECLARE i INT DEFAULT 8;
    DECLARE tipo_mant VARCHAR(20);
    DECLARE descrip VARCHAR(255);
    
    WHILE i <= 1000 DO
        SET tipo_mant = ELT(FLOOR(1 + RAND() * 3), 'preventivo','correctivo','reparacion');
        SET descrip = ELT(FLOOR(1 + RAND() * 12),
            'Cambio de aceite y filtro','Ajuste de frenos','Alineación y balanceo','Revisión de suspensión',
            'Cambio de llantas','Limpieza de inyectores','Diagnóstico eléctrico','Cambio de batería',
            'Reparación de transmisión','Servicio general','Revisión de dirección','Cambio de correas'
        );
        
        INSERT INTO mantenimiento (id_vehiculo, tipo, descripcion, costo, fecha)
        VALUES (
            FLOOR(1 + RAND() * 1000),
            tipo_mant,
            descrip,
            ROUND(500 + RAND() * 10000, 2),
            DATE_ADD('2024-01-01', INTERVAL FLOOR(RAND() * 365) DAY)
        );
        SET i = i + 1;
    END WHILE;
END//
DELIMITER ;

-- Generar 1000 consumos adicionales
DELIMITER //
-- Procedimiento: genera consumos de combustible variados
CREATE PROCEDURE generar_consumos()
BEGIN
    DECLARE i INT DEFAULT 16;
    DECLARE mat VARCHAR(20);
    DECLARE tipo_comb VARCHAR(30);
    DECLARE litros_val DECIMAL(10,2);
    
    WHILE i <= 1000 DO
        SET mat = (SELECT matricula FROM vehiculo ORDER BY RAND() LIMIT 1);
        SET tipo_comb = ELT(FLOOR(1 + RAND() * 4), 'Gasolina','Diésel','Eléctrico','Gas');
        SET litros_val = ROUND(20 + RAND() * 120, 2);
        
        INSERT INTO consumo (matricula, litros, fecha, tipo_combustible, costo)
        VALUES (
            mat,
            litros_val,
            DATE_ADD('2024-01-01', INTERVAL FLOOR(RAND() * 365) DAY),
            tipo_comb,
            ROUND(litros_val * (18 + RAND() * 6), 2)
        );
        SET i = i + 1;
    END WHILE;
END//
DELIMITER ;

-- Generar 1000 incidentes adicionales
DELIMITER //
-- Procedimiento: genera incidentes habituales
CREATE PROCEDURE generar_incidentes()
BEGIN
    DECLARE i INT DEFAULT 4;
    DECLARE mat VARCHAR(20);
    DECLARE tipos_inc VARCHAR(255) DEFAULT 'accidente,infracción,daño,falla mecánica,robo';
    DECLARE descrip VARCHAR(255);
    
    WHILE i <= 1000 DO
        SET mat = (SELECT matricula FROM vehiculo ORDER BY RAND() LIMIT 1);
        SET descrip = ELT(FLOOR(1 + RAND() * 10),
            'Choque leve en intersección','Exceso de velocidad','Raspones en carrocería','Falla en sistema de frenos',
            'Robo de espejo','Pinchazo de llanta','Luces dañadas','Golpe en defensa',
            'Motor sobrecalentado','Infracción de estacionamiento'
        );
        
        INSERT INTO incidente (matricula, tipo, fecha, descripcion)
        VALUES (
            mat,
            ELT(FLOOR(1 + RAND() * 5), 'accidente','infracción','daño','falla mecánica','robo'),
            DATE_ADD('2024-01-01', INTERVAL FLOOR(RAND() * 365) DAY),
            descrip
        );
        SET i = i + 1;
    END WHILE;
END//
DELIMITER ;

-- Generar 1000 licencias adicionales
DELIMITER //
-- Procedimiento: genera licencias con tipos y vigencias realistas
CREATE PROCEDURE generar_licencias()
BEGIN
    DECLARE i INT DEFAULT 5;
    DECLARE tipo_lic VARCHAR(5);
    DECLARE fecha_em DATE;
    
    WHILE i <= 1000 DO
        SET tipo_lic = ELT(FLOOR(1 + RAND() * 12), 'A','A1','A2','B','B1','C','D','E','F','G','H','AM');
        SET fecha_em = DATE_ADD('2018-01-01', INTERVAL FLOOR(RAND() * 2190) DAY);
        
        INSERT INTO licencia (id_conductor, tipo, fecha_emision, fecha_vencimiento)
        VALUES (
            FLOOR(1 + RAND() * 1000),
            tipo_lic,
            fecha_em,
            DATE_ADD(fecha_em, INTERVAL (3 + FLOOR(RAND() * 5)) YEAR)
        );
        SET i = i + 1;
    END WHILE;
END//
DELIMITER ;

-- Generar 1000 evaluaciones adicionales
DELIMITER //
-- Procedimiento: genera evaluaciones con comentarios frecuentes
CREATE PROCEDURE generar_evaluaciones()
BEGIN
    DECLARE i INT DEFAULT 4;
    DECLARE comentarios_pool VARCHAR(255) DEFAULT 'Puntual y responsable,Buen trato con clientes,Mejora en eficiencia,Atento a señales,Manejo defensivo,Necesita capacitación,Excelente rendimiento,Consumo moderado,Cuida el vehículo,Organiza rutas';
    
    WHILE i <= 1000 DO
        INSERT INTO evaluacion (id_conductor, fecha, puntuacion, comentarios)
        VALUES (
            FLOOR(1 + RAND() * 1000),
            DATE_ADD('2024-01-01', INTERVAL FLOOR(RAND() * 365) DAY),
            FLOOR(5 + RAND() * 6),
            ELT(FLOOR(1 + RAND() * 10), 'Puntual y responsable','Buen trato con clientes','Mejora en eficiencia','Atento a señales','Manejo defensivo','Necesita capacitación','Excelente rendimiento','Consumo moderado','Cuida el vehículo','Organiza rutas')
        );
        SET i = i + 1;
    END WHILE;
END//
DELIMITER ;

-- Ejecutar todos los procedimientos
CALL generar_flotas();
CALL generar_usuarios();
CALL generar_conductores();
CALL generar_vehiculos();
CALL generar_ordenes();
CALL generar_viajes();
CALL generar_mantenimientos();
CALL generar_consumos();
CALL generar_incidentes();
CALL generar_licencias();
CALL generar_evaluaciones();

-- Limpiar procedimientos
DROP PROCEDURE IF EXISTS generar_flotas;
DROP PROCEDURE IF EXISTS generar_usuarios;
DROP PROCEDURE IF EXISTS generar_conductores;
DROP PROCEDURE IF EXISTS generar_vehiculos;
DROP PROCEDURE IF EXISTS generar_ordenes;
DROP PROCEDURE IF EXISTS generar_viajes;
DROP PROCEDURE IF EXISTS generar_mantenimientos;
DROP PROCEDURE IF EXISTS generar_consumos;
DROP PROCEDURE IF EXISTS generar_incidentes;
DROP PROCEDURE IF EXISTS generar_licencias;
DROP PROCEDURE IF EXISTS generar_evaluaciones;