CREATE DATABASE dbproyectosdr;
USE dbproyectosdr;

CREATE TABLE ambulancia (
    id_ambulancia INT NOT NULL AUTO_INCREMENT,
    placa VARCHAR(7) NOT NULL,
    marca_ambulancia VARCHAR(20) NOT NULL,
    modelo_ambulancia VARCHAR(20) NOT NULL,
    CONSTRAINT pk_id_ambulancia PRIMARY KEY (id_ambulancia)
);

CREATE TABLE equipo (
    id_equipo INT NOT NULL AUTO_INCREMENT,
    numero_serial VARCHAR(50) NOT NULL,
    marca_equipo VARCHAR(20) NOT NULL,
    modelo_equipo VARCHAR(20) NOT NULL,
    CONSTRAINT pk_id_equipo PRIMARY KEY (id_equipo)
);
    id_conductor INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(20) NOT NULL,
    apellido VARCHAR(20) NOT NULL,
    fecha_nacimiento DATE,
    usuario VARCHAR(20) NOT NULL,
    contrasena VARCHAR(100) NOT NULL,
    CONSTRAINT pk_id_conductor PRIMARY KEY (id_conductor)
);

CREATE TABLE ambulancia_equipo (
    id_ambulancia INT,
    id_equipo INT,
    fecha_instalacion DATE,
    CONSTRAINT fk_id_ambulancia_ae FOREIGN KEY (id_ambulancia)
        REFERENCES ambulancia (id_ambulancia),
    CONSTRAINT fk_id_equipo_ae FOREIGN KEY (id_equipo)
        REFERENCES equipo (id_equipo)
);

CREATE TABLE grabacion (
    id_grabacion INT NOT NULL AUTO_INCREMENT,
    id_equipo INT,
    path_grabacion VARCHAR(100),
    fecha_grabacion DATE,
    hora_grabacion TIME,
    CONSTRAINT pk_id_grabacion PRIMARY KEY (id_grabacion),
    CONSTRAINT fk_id_equipo_g FOREIGN KEY (id_equipo)
        REFERENCES equipo (id_equipo)
);

CREATE TABLE estado (
    id_estado INT NOT NULL AUTO_INCREMENT,
    id_equipo INT,
    fecha_encendido DATE,
    hora_encendido TIME,
    fecha_apagado DATE,
    hora_apagado TIME,
    CONSTRAINT pk_id_estado PRIMARY KEY (id_estado),
    CONSTRAINT fk_id_equipo_e FOREIGN KEY (id_equipo)
        REFERENCES equipo (id_equipo)
);

SELECT MAX(id_estado) FROM estado WHERE id_equipo = 1
INSERT INTO estado (id_equipo, fecha_encendido, hora_encendido) VALUES (1,'2019-06-05','5:40')
select * from estado
UPDATE estado SET hora_apagado = '6:40', fecha_apagado ='2019-06-05' WHERE id_equipo = 1 ORDER BY id_estado DESC LIMIT 1