# Sistema de Análisis de Formación Corporativa

## 1. Introducción

### 1.1 Contexto
Este proyecto implementa un sistema de ingesta y análisis de datos para una empresa de formación corporativa. El sistema integra datos de dos fuentes principales:

- Base de datos operativa PostgreSQL que gestiona:
  - Cursos y su información
  - Registro de ventas
  - Actividades de los participantes
- HubSpot como CRM para gestionar la información de empresas clientes

El destino principal de los datos es DuckDB, elegido por su eficiencia para análisis, con la posibilidad de usar PostgreSQL como destino alternativo para el entorno productivo.

### 1.2 Estructura de la Base de Datos
El esquema de la base de datos operativa está definido en [`schema.sql`](schema.sql) e incluye las siguientes tablas:

- `clientes`: Información de empresas clientes
- `cursos`: Catálogo de cursos disponibles
- `ventas`: Registro de ventas de cursos
- `participantes`: Personas que asisten a los cursos
- `actividades_participantes`: Seguimiento de actividades durante el curso

El esquema incluye:
- Claves primarias y foráneas para mantener la integridad referencial
- Campos de auditoría (fecha_registro, updated_at)
- Índices para optimizar el rendimiento
- Trigger para actualización automática de timestamps

## 2. Estrategias de Ingesta

### 2.1 Extracción Directa desde PostgreSQL

#### 2.1.1 Carga Completa - Tabla de Cursos
- **Justificación**: La extracción completa es apropiada para la tabla de cursos porque:
  - Es una tabla de dimensión con pocos registros
  - Los datos son relativamente estáticos (los cursos no cambian frecuentemente)
  - No requiere tracking de cambios históricos
  - El volumen de datos es pequeño, haciendo eficiente la carga completa
- **Implementación**: [`cargar_tabla_unica()`](tutorial_dlthub.py#L7-L30)

#### 2.1.2 Carga Incremental - Tabla de Ventas
- **Justificación**: La extracción incremental es ideal para ventas porque:
  - Es una tabla que crece constantemente con nuevos registros
  - Los registros existentes pueden actualizarse (ej: cambios de estado, fechas)
  - El campo updated_at permite identificar registros nuevos o modificados
  - Optimiza recursos al procesar solo los cambios desde la última ejecución
  - El volumen de datos históricos puede ser significativo
- **Implementación**: [`cargar_tabla_unica_incremental()`](tutorial_dlthub.py#L32-L55)

#### 2.1.3 CDC - Tabla actividades_participantes
- **Justificación**: CDC es la mejor estrategia para actividades de participantes porque:
  - Son eventos en tiempo real que necesitan capturarse inmediatamente
  - El volumen de eventos puede ser alto (múltiples actividades por participante)
  - Es crítico mantener el orden cronológico exacto de las actividades
  - Permite análisis en tiempo real del engagement de los participantes
  - Los datos nunca se actualizan, solo se insertan nuevos registros
- **Implementación**: [`replicate_actividades_participantes()`](tutorial_dlthub.py#L57-L90)

### 2.2 Integración con HubSpot
- Extracción de datos de empresas mediante API oficial de HubSpot
- Uso del conector verificado de DLT para HubSpot
- **Implementación**: [`carga_companies_hubspot()`](tutorial_dlthub.py#L92-L115)

## 3. Guía de Implementación

### 3.1 Instalación y Configuración Inicial
Seguir los pasos de instalación de [DLT](https://dlthub.com/docs/reference/installation):

1. Crear entorno virtual (ejemplo Windows):
```bash
python -m venv D:\Python\venv\dlthub
```

2. Activar entorno:
```bash
D:\Python\venv\dlthub\Scripts\Activate.ps1
```

3. Instalar DLT:
```bash
pip install dlt
```

Nota: En Windows, si hay errores de instalación, instalar [Visual C++ Build Tools](https://visualstudio.microsoft.com/es/visual-cpp-build-tools/) con la opción "Desktop development with C++"

### 3.2 Configuración del Proyecto Base

#### 3.2.1 Inicialización
Basándonos en el [tutorial oficial de SQL Database](https://dlthub.com/docs/tutorial/sql-database):

1. Inicializar proyecto:
```bash
dlt init sql_database duckdb
```

Esto genera la estructura:
```
├── .dlt
│   ├── config.toml
│   └── secrets.toml
├── sql_database_pipeline.py
└── requirements.txt
```

#### 3.2.2 Modificación de Archivos
1. Creamos un script para nuestro pipeline `tutorial_dlthub.py`
2. Creamos una función `cargar_tabla_unica` tomando como referencia `load_select_tables_from_database` de `sql_database_pipeline.py`
3. Modificamos las credenciales en `secrets.toml`
4. Momento de instalar más librerías, en `requirements.txt` dlt nos dejó los paquetes que va a utilizar, además como vamos a conectarnos a Postgres, la librería que utiliza dltHub por detrás (SQL Alchemy) necesita un paquete adicional, lo agregamos al archivo:
```toml
psycopg2-binary>=2.9.0
```
5. Ejecutamos:
```bash
pip install -r requirements.txt
```

#### 3.2.3 Prueba Inicial
1. Ya podemos probar:
```bash
python tutorial_dlthub.py
```

2. Podemos chequear el destino (tutorial_dlt.duckdb) con dbeaver

3. Si volvemos a ejecutar tenemos que ver la misma cantidad de registros porque el write-disposition es replace. [Documentación de write_disposition](https://dlthub.com/docs/general-usage/incremental-loading#choosing-a-write-disposition)

### 3.3 Implementación de Estrategias

#### 3.3.1 Carga Incremental
1. Ahora usamos otra estrategia, incremental con otra tabla. `load_select_tables_from_database` tiene un ejemplo, lo adaptamos para crear `cargar_tabla_unica_incremental()`. Más info en [Documentación avanzada de SQL Database](https://dlthub.com/docs/dlt-ecosystem/verified-sources/sql_database/advanced)

#### 3.3.2 Destino PostgreSQL
1. Por último usaremos postgres como destino, sería nuestro entorno productivo. Tenemos que agregar las credenciales en el `secrets.toml` en una sección `[destination.postgres.credentials]`
2. Creamos `cargar_tabla_unica_postgres()` modificando `destination='postgres'`. Lo ideal aquí sería reutilizar `cargar_tabla_unica` manejando nuestros entornos con parámetros y variables, lo mantenemos en una función aparte para que el curso sea más claro.

#### 3.3.3 CDC con PostgreSQL
Ya hicimos las cargas más sencillas, ahora vamos a algo más interesante, CDC mediante replicación en postgres [Guía de configuración de replicación](https://dlthub.com/docs/dlt-ecosystem/verified-sources/pg_replication):

1. Tenemos que tener un usuario en la base con permisos para utilizar replication. [Guía de configuración de replicación](https://dlthub.com/docs/dlt-ecosystem/verified-sources/pg_replication#setup-guide)

2. Al igual que antes, inicializamos el proyecto, podemos seguir usando el que tenemos, en ese caso se modificaran los archivos existentes y se agregarán las cosas que falten:
```bash
dlt init pg_replication duckdb
```

3. Vemos que en `secrets.toml` se agregó una nueva sección `[sources.pg_replication.credentials]`, debemos completarla con los datos del usuario configurado en el punto 1.

4. Nos basamos en `replicate_single_table()` del archivo creado de ejemplo (`pg_replication_pipeline.py`) para crear nuestra propia función `replicate_actividades_participantes()` en `tutorial_dlthub.py`. Las modificaciones que le hacemos son:
   - En la creación del pipeline `dev_mode=False` para que no utilice datos de prueba
   - En `init_replication` `reset=False` para que no recree las publicaciones en Postgres
   - Seteamos `schema_name` y `table_names` para que coincidan con nuestra tabla

5. Ejecutamos una primera vez para que dlt se encargue de crear la publicación y el slot en Postgres.

6. A partir de ahí, cualquier cambio que hagamos en la tabla en términos de insert, update o delete dlt lo va a capturar al volver a ejecutar el script.

#### 3.3.4 Integración con HubSpot
Última ingesta, nos salimos de las bases de datos y vamos a una aplicación saas, particularmente un CRM (HubSpot). Para simplificar el caso, solamente vamos a traer datos de la entidad de companies:

1. En primer lugar tenemos que crear una aplicación privada en hubspot y asignarle los permisos necesarios ([Documentación de HubSpot](https://developers.hubspot.com/docs/guides/apps/private-apps/overview)), ahí obtendremos un token para autenticar a la api.

2. Volvemos a hacer uso del init ya que hubspot es una fuente de datos verificada en dltHub:
```bash
dlt init hubspot duckdb
```

3. Ahora tenemos una nueva sección en el `secrets.toml`: `[sources.hubspot]`, ahí debemos poner el token que generamos en el punto 1.

4. Agregamos una función `carga_companies_hubspot` a `tutorial_dlthub.py` tomando como referencia `load_crm_data` de `hubspot_pipeline.py`

5. Ejecutamos y si todo fue ok, en la misma base de duckdb tendremos los datos de las Empresas de HubSpot 