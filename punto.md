# Diagnóstico y propuesta de solución para estabilizar las pruebas

## Contexto

La suite combina pruebas unitarias, integraciones con MLflow/DVC y pruebas del
frontend. El diagnóstico recibido apunta a tres grupos de fallos:

1. mocks de archivos demasiado amplios en las pruebas del backend;
2. contratos de pruebas desactualizados frente a la validación actual de la API;
3. un pipeline de CI que continúa hasta SonarCloud aunque las pruebas del
   backend hayan fallado.

La hipótesis principal es razonable, pero no todos sus puntos están confirmados
por el estado actual del repositorio. Antes de modificar producción conviene
separar la causa demostrada de las recomendaciones que todavía deben validarse
con la salida exacta de `pytest`, ESLint y SonarCloud.

## Evidencia observada

### 1. Los mocks globales de `open` existen realmente

El test de PatchTSMixer usa:

```python
@patch('builtins.open', new_callable=mock_open)
```

en [test_patchtsmixer_integration.py](DREAM-ML-backend/GEML/tests/apiTimeSeries_tests/test_patchtsmixer_integration.py).
También hay usos del mismo patrón en [test_services_train_model_logic.py](DREAM-ML-backend/GEML/tests/apiTimeSeries_tests/test_services_train_model_logic.py)
y en varios tests de `api`.

Esto confirma un riesgo real: mientras el test está activo, cualquier código
que resuelva `open` mediante `builtins` recibe el mock, no solo el código que
escribe o lee el dataset. MLflow puede intentar leer `alembic.ini`,
configuraciones o metadatos durante ese intervalo. Si recibe el contenido
incorrecto del mock, puede producir errores como
`configparser.MissingSectionHeaderError`.

No obstante, la presencia del decorador por sí sola no demuestra cuál test
causa el error concreto. Hay que reproducir el fallo con el traceback y aislar
el primer test que lo provoca.

### 2. Hay parches con rutas probablemente incorrectas

Algunos tests usan:

```python
@patch('pd.read_csv')
```

La ruta correcta normalmente debe ser la ruta donde el código bajo prueba
resuelve el símbolo, por ejemplo `apiTimeSeries.services.pd.read_csv` si
`services.py` importó `pandas as pd`. `pd` no suele ser un módulo importable
por sí mismo, así que este patrón debe corregirse o confirmarse contra la
implementación real.

En cambio, otros tests ya usan la forma más específica
`api.services.pd.read_csv`, que sirve como referencia para la corrección.

### 3. La configuración de ESLint ya contiene varias soluciones propuestas

El archivo [eslint.config.js](DREAM-ML-frontend/frontend/eslint.config.js)
ya incluye:

- `react.configs['jsx-runtime'].rules`;
- `globals.node` junto con `globals.browser`;
- `'react/prop-types': 'off'`;
- `'react/no-unescaped-entities': 'off'`.

Por eso, añadir nuevamente esas reglas no parece ser la acción pendiente en
este estado del árbol. Si ESLint aún informa esos errores, las causas
alternativas a revisar son una configuración cargada distinta, una ejecución
desde otro directorio, cambios locales no incluidos en CI o una versión
distinta de dependencias. La configuración aparece modificada en el worktree,
por lo que también hay que confirmar si esos cambios están committed o son
parte de una corrección local.

`prop-types` no está en [package.json](DREAM-ML-frontend/frontend/package.json),
pero la regla está desactivada. Instalarlo solo sería necesario si el equipo
decide volver a exigir validación PropTypes; no debe instalarse como respuesta
automática si la estrategia es React 18 con otra solución de tipos.

### 4. El workflow permite continuar después de un fallo de backend

En [sonarcloud.yml](.github/workflows/sonarcloud.yml), el paso de pruebas:

- tiene `continue-on-error: true`;
- ejecuta `pytest` con `set +e`;
- guarda los reportes;
- termina con `exit "$test_status"`.

El `exit` conserva el código de fallo del test, pero `continue-on-error: true`
hace que el job continúe con lint, build y SonarCloud. Esto permite publicar un
análisis estático con pruebas fallidas o cobertura incompleta. Es un problema
confirmado de calidad del pipeline.

### 5. No existe actualmente un aislamiento global de MLflow

El [conftest.py](DREAM-ML-backend/GEML/tests/conftest.py) raíz define fixtures
de directorios, datos y objetos mock, pero no configura una URI temporal de
MLflow. Eso no prueba por sí mismo que MLflow esté escribiendo en un directorio
incorrecto, aunque sí deja abierta esa posibilidad en tests que no mockean
completamente MLflow.

Un fixture `autouse` que cree una base SQLite para cada prueba puede ser
demasiado costoso y puede introducir migraciones repetidas. Para pruebas
unitarias es preferible mockear la frontera de MLflow; para pruebas de
integración, usar una URI temporal explícita y una inicialización controlada.

## Solución propuesta

### Fase 1: reproducir y clasificar los fallos

1. Ejecutar primero los archivos afectados de forma aislada:

   ```bash
   cd DREAM-ML-backend/GEML
   pytest tests/apiTimeSeries_tests/test_patchtsmixer_integration.py -vv -ra
   pytest tests/apiTimeSeries_tests/test_services_train_model_logic.py -vv -ra
   ```

2. Guardar el primer traceback de MLflow y el nombre exacto del test.
3. Ejecutar frontend desde
   `DREAM-ML-frontend/frontend`:

   ```bash
   npm run lint
   npm run build
   ```

4. No cambiar todavía el código de producción por un fallo que solo aparezca
   en la configuración de los mocks.

### Fase 2: reducir el alcance de los mocks

La corrección preferida es parchear el símbolo en el módulo que lo usa, no
secuestrar `builtins.open` durante toda la prueba. Por ejemplo, si el código
usa `pandas.read_csv`, parchear:

```python
@patch('apiTimeSeries.services.pd.read_csv')
```

Para operaciones de escritura, se debe parchear una abstracción propia del
servicio si existe. Si el servicio usa directamente `open` y no hay un alias
de módulo, hay dos opciones seguras:

1. extraer una pequeña función de lectura/escritura al módulo del servicio y
   parchear esa función;
2. conservar temporalmente el parche de `builtins.open`, pero delegar todas
   las rutas no relacionadas con el dataset al `open` real.

No se debe devolver siempre `{"steps": []}` o un `MagicMock` para cualquier
archivo. El mock debe distinguir el archivo objetivo y dejar pasar los
archivos que MLflow necesita leer. También hay que corregir los decoradores
`@patch('pd.read_csv')` a la ruta de importación efectiva.

Después de cada corrección, comprobar que el test verifica el comportamiento
que pretende probar y no solo que el mock fue llamado.

### Fase 3: definir una frontera explícita para MLflow

Separar las pruebas en dos categorías:

- **Unitarias:** mockear `set_tracking_uri`, `get_experiment_by_name`,
  `start_run`, logging y creación de datasets de MLflow. No deben depender de
  Alembic, SQLite ni del estado del usuario.
- **Integración:** usar un directorio temporal exclusivo, una URI SQLite
  temporal o un backend de MLflow de pruebas, y limpiar el run activo al
  terminar.

Si se necesita un fixture de aislamiento, debe restaurar siempre el estado
anterior y finalizar runs activos. La implementación debe acordarse con la
versión instalada de MLflow, porque `set_tracking_uri` no garantiza por sí
solo que el esquema de una base nueva esté inicializado. Una opción más
predecible es configurar la URI mediante fixture y ejecutar la inicialización
de MLflow una vez por sesión de integración, no una migración por test.

### Fase 4: actualizar los contratos de las pruebas

Si `train_model_logic` valida el archivo CSV antes del directorio, el test debe
construir una entrada que supere esa validación antes de comprobar el error
posterior. Esto no significa añadir datos artificiales indiscriminadamente:

- para probar un directorio inexistente, usar un archivo válido y hacer que
  solo `os.path.exists` devuelva `False` para el directorio;
- para probar un algoritmo inválido, usar un archivo válido y un directorio
  válido, y después afirmar `ValueError`;
- para probar un CSV ausente o inválido, dejar esas condiciones como tests
  independientes y afirmar el error de validación correspondiente.

Así cada prueba tiene una sola causa de fallo y no depende accidentalmente del
orden de validaciones internas.

### Fase 5: hacer que CI falle de forma honesta

Eliminar `continue-on-error: true` del paso de backend. También puede
eliminarse `set +e` si no se necesita generar reportes después de un fallo.
Si se quieren conservar los reportes aun cuando fallen los tests, usar un
patrón explícito:

1. ejecutar pytest y guardar su código;
2. generar los reportes con una condición que tolere únicamente el paso de
   generación;
3. subir artefactos con `if: always()`;
4. fallar el job después de subir los artefactos;
5. permitir SonarCloud solo si backend, lint y build terminaron correctamente.

La cobertura no debe interpretarse como válida si la ejecución de pruebas no
terminó correctamente.

## Orden recomendado de implementación

1. Reproducir el fallo y conservar los tracebacks.
2. Corregir rutas `patch` inválidas.
3. Reducir los parches de `builtins.open`.
4. Separar tests unitarios de integración de MLflow.
5. Actualizar los tests cuyo contrato de validación cambió.
6. Quitar `continue-on-error` y verificar que CI se detiene ante fallos.
7. Revisar ESLint solo después de confirmar la configuración efectiva que usa
   CI; no instalar `prop-types` ni editar componentes si la regla continúa
   desactivada.

## Criterios de aceptación

- Los tests de PatchTSMixer pasan sin interceptar archivos internos de MLflow.
- Ningún test usa `@patch('pd.read_csv')` si esa no es la ruta de importación
  real.
- Los tests unitarios no crean ni reutilizan accidentalmente el estado global
  de MLflow.
- Los errores de CSV, directorio, algoritmo y experimento de MLflow tienen
  tests separados y códigos/mensajes explícitos.
- `pytest` y `npm run lint` terminan con código cero en local antes de SonarCloud.
- Un fallo de backend hace fallar el job de CI y evita un análisis Sonar basado
  en cobertura incompleta.

## Puntos para discutir con un modelo más avanzado

1. ¿El traceback muestra que el error de Alembic ocurre dentro de uno de los
   tests con `mock_open`, o proviene de una fixture/configuración global?
2. ¿`TrainModelService` usa `open` directamente, una función importada o un
   helper de archivos? La respuesta determina la ruta correcta del parche.
3. ¿Qué tests deben ser realmente de integración con MLflow y cuáles pueden
   aislarse completamente?
4. ¿La validación del CSV antes del directorio y del algoritmo es el contrato
   intencional de la API? Si no lo es, debe cambiarse la producción y no solo
   los tests.
5. ¿El cambio actual de ESLint está comprometido y es el mismo que ejecuta
   GitHub Actions?
6. ¿Se desea que SonarCloud se ejecute únicamente con todas las verificaciones
   verdes, o se necesitan reportes diagnósticos aun cuando la calidad falle?

