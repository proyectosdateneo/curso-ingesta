import dlt

from dlt.sources.sql_database import sql_database

from pg_replication import replication_resource
from pg_replication.helpers import init_replication

from hubspot import hubspot

def cargar_tabla_unica() -> None:
    """
    Carga una tabla específica desde una base de datos SQL a DuckDB.
    
    Esta función realiza las siguientes operaciones:
    1. Crea un pipeline de datos hacia DuckDB
    2. Extrae los datos de la tabla 'cursos'
    3. Reemplaza completamente los datos existentes en el destino
    """
    # Configurar el pipeline de datos
    # - pipeline_name: nombre de la base de datos que se creará en DuckDB
    # - dataset_name: nombre del esquema donde se almacenarán las tablas
    pipeline = dlt.pipeline(
        pipeline_name="tutorial_dlt",
        destination='duckdb',
        dataset_name="replica"
    )

    # Crear una conexión a la base de datos origen y seleccionar la tabla 'cursos'
    # Las credenciales se tomarán automáticamente del archivo .dlt/secrets.toml
    tabla_curso = sql_database().with_resources("cursos")

    # Ejecutar el pipeline:
    # - write_disposition="replace": si la tabla existe, se eliminará y creará nuevamente
    info = pipeline.run(tabla_curso, write_disposition="replace")

    # Mostrar el resultado de la operación (número de filas procesadas, errores, etc.)
    print(info)

def cargar_tabla_unica_incremental() -> None:
    """
    Carga incrementalmente los datos de una tabla SQL a DuckDB.
    
    Esta función realiza las siguientes operaciones:
    1. Crea un pipeline de datos hacia DuckDB
    2. Configura la carga incremental usando el campo 'updated_at'
    3. Fusiona los nuevos datos con los existentes en el destino
    
    Nota: La carga incremental solo procesará los registros que han sido 
    actualizados desde la última ejecución.
    """
    # Configurar el pipeline de datos usando el mismo nombre de base de datos
    # para mantener consistencia con cargas anteriores
    pipeline = dlt.pipeline(
        pipeline_name="tutorial_dlt",
        destination='duckdb',
        dataset_name="replica"  # esquema en duckdb
    )

    # Obtener la tabla "ventas" y configurar la carga incremental
    tablas = sql_database().with_resources("ventas")

    # Configurar la carga incremental usando el campo 'updated_at'
    # Esto asegura que solo se procesen los registros nuevos o modificados
    tablas.ventas.apply_hints(incremental=dlt.sources.incremental("updated_at"))

    # Ejecutar el pipeline:
    # - write_disposition="merge": fusiona los nuevos datos con los existentes
    info = pipeline.run(tablas, write_disposition="merge")

    # Mostrar el resultado de la operación
    print(info)

def cargar_tabla_unica_postgres() -> None:
    """
    Carga una tabla específica desde una base de datos SQL a PostgreSQL.
    
    Esta función realiza las siguientes operaciones:
    1. Crea un pipeline de datos hacia PostgreSQL
    2. Extrae los datos de la tabla 'cursos'
    3. Reemplaza completamente los datos existentes en el destino
    
    Nota: A diferencia de las funciones anteriores, esta utiliza PostgreSQL 
    como destino en lugar de DuckDB.
    """
    # Configurar el pipeline de datos hacia PostgreSQL
    pipeline = dlt.pipeline(
        pipeline_name="tutorial_dlt",
        destination='postgres',
        dataset_name="replica"  # esquema en postgres
    )

    # Crear una conexión a la base de datos origen y seleccionar la tabla 'cursos'
    # Las credenciales se tomarán del archivo .dlt/secrets.toml
    tabla_curso = sql_database().with_resources("cursos")

    # Ejecutar el pipeline:
    # - write_disposition="replace": si la tabla existe, se eliminará y creará nuevamente
    info = pipeline.run(tabla_curso, write_disposition="replace")

    # Mostrar el resultado de la operación
    print(info)

def replicate_actividades_participantes() -> None:
    """
    Replica en tiempo real los cambios de la tabla 'actividades_participantes' desde PostgreSQL a DuckDB.
    
    Esta función realiza las siguientes operaciones:
    1. Crea un pipeline de datos hacia DuckDB
    2. Inicializa la replicación lógica en PostgreSQL
    3. Configura un slot de replicación y una publicación
    4. Captura y replica los cambios en tiempo real
    
    Requisitos:
    - El usuario de PostgreSQL debe tener el atributo REPLICATION
    - La tabla 'actividades_participantes' debe estar en el esquema 'public'
    
    Nota: Esta función utiliza replicación lógica de PostgreSQL para capturar
    inserciones, actualizaciones y eliminaciones en tiempo real.
    """
    # Configurar el pipeline de datos hacia DuckDB
    # - dev_mode=False: necesario para mantener el estado de la replicación
    dest_pl = dlt.pipeline(
        pipeline_name="tutorial_dlt",
        destination='duckdb',
        dataset_name="replica",
        dev_mode=False,
    )

    # Configurar la replicación lógica en PostgreSQL
    # - slot_name: identificador único para el slot de replicación
    # - pub_name: nombre de la publicación que contendrá los cambios
    slot_name = "dlt_slot"
    pub_name = "dlt_publication"

    # Inicializar la replicación para la tabla origen
    # - schema_name: esquema donde se encuentra la tabla
    # - table_names: tabla(s) a replicar
    # - reset=False: mantener la configuración existente si ya existe
    init_replication(
        slot_name=slot_name,
        pub_name=pub_name,
        schema_name="public",
        table_names="actividades_participantes",
        reset=False,
    )

    # Crear y ejecutar el recurso de replicación
    # Este recurso capturará todos los cambios (INSERT, UPDATE, DELETE)
    # que ocurran en la tabla 'participantes'
    changes = replication_resource(slot_name, pub_name)
    dest_pl.run(changes)

def carga_companies_hubspot() -> None:
    """
    Carga los datos de empresas desde HubSpot CRM hacia DuckDB.
    
    Esta función realiza las siguientes operaciones:
    1. Crea un pipeline de datos hacia DuckDB
    2. Se conecta a la API de HubSpot utilizando credenciales configuradas
    3. Extrae los datos de todas las empresas (companies)
    4. Almacena los datos en la base de datos de destino
    
    Requisitos:
    - Token de acceso de HubSpot configurado en .dlt/secrets.toml
    - Permisos para acceder a la información de empresas en HubSpot
    
    Nota: Esta función utiliza el conector oficial de HubSpot para DLT
    para extraer los datos de manera eficiente y segura.
    """
    # Configurar el pipeline de datos hacia DuckDB
    # - pipeline_name: identificador único del pipeline
    # - dataset_name: nombre del esquema donde se almacenarán los datos
    # - destination: tipo de base de datos de destino (duckdb)
    pipeline = dlt.pipeline(
        pipeline_name="tutorial_dlt",
        dataset_name="replica",
        destination='duckdb',
    )

    # Ejecutar el pipeline utilizando el conector de HubSpot
    # - hubspot(): inicializa el conector con las credenciales configuradas
    # - with_resources("companies"): selecciona específicamente la tabla de empresas
    info = pipeline.run(hubspot().with_resources("companies"))

    # Mostrar información sobre la ejecución del pipeline
    # Incluye detalles como número de registros procesados, errores si los hubo, etc.
    print(info)

if __name__ == "__main__":
    # Descomentar la función que se desea ejecutar
    
    cargar_tabla_unica()
    # cargar_tabla_unica_incremental()
    # cargar_tabla_unica_postgres()
    # replicate_actividades_participantes()
    # carga_companies_hubspot()
