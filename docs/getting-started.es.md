# Primeros pasos con loretools

Esta guía es para investigadores que usan **Claude Co-Work** (Proyectos de Claude con acceso a archivos). No se requiere experiencia con la terminal — tu agente de IA gestiona todas las operaciones de shell.

---

## ¿Qué es una colección?

Una **colección** es una única carpeta que contiene todo lo que loretools necesita:

- `lore` — el binario que ejecuta el agente
- `.loretools/config.json` — tus preferencias y configuración
- `library.json` — tu biblioteca de referencias
- `files/` — archivos PDF y documentos vinculados a referencias
- `staging/` — referencias en espera de revisión y fusión

Puedes crear una colección por proyecto de investigación (o una colección compartida entre proyectos — tú decides).

---

## Primera sesión: configurar tu colección

### 1. Descarga el zip de la versión

Ve a la [página de Releases](https://github.com/abrahambahez/loretools/releases) y descarga el zip para tu plataforma:

- **macOS (Apple Silicon):** `scht-X.Y.Z-macos-arm64.zip`
- **Linux:** `scht-X.Y.Z-linux-x86_64.zip`
- **Windows:** `scht-X.Y.Z-windows-x86_64.zip`

### 2. Prepara tu carpeta de colección

Crea o elige una carpeta para tu colección de investigación. Esta carpeta contendrá todas tus referencias y archivos — guárdala en un lugar que persista entre sesiones (por ejemplo, tu carpeta de Documentos, no un área de carga temporal).

### 3. Abre Claude Co-Work y monta tu carpeta de colección

Abre Claude Projects y conecta tu carpeta de colección para que el agente pueda leer y escribir archivos allí.

### 4. Sube el zip de la versión

Sube el archivo zip que descargaste en el paso 1 a tu sesión de Co-Work.

### 5. Instala la skill `loretools-manager`

Descarga el zip de la skill desde la misma página de Releases (`loretools-loretools-manager-es-X.Y.Z.zip` para español o la variante `en` para inglés) e instálala. Dile al agente:

> "Por favor instala la skill loretools-manager desde este zip."

### 6. Pide al agente que complete la configuración

Una vez instalada la skill, di:

> "Configura loretools en mi carpeta de colección."

El agente:
1. Descomprimirá `lore` y lo hará ejecutable
2. Lo ejecutará una vez para crear automáticamente `.loretools/config.json`
3. Verificará que la colección esté operativa

### 7. Verifica que todo funciona

Dile al agente:

> "Lista mis referencias."

Deberías ver una respuesta como `{"ok": true, "references": [], ...}`. Tu colección está lista.

---

## Sesiones posteriores

Cada vez que abras una nueva sesión de Co-Work:

1. Abre Claude Projects y monta tu carpeta de colección
2. Pide al agente que verifique la colección:

   > "Verifica que loretools esté funcionando."

   El agente comprueba que `lore` esté presente y que la configuración sea válida.

3. Comienza a trabajar — añade referencias, obtén metadatos, fusiona elementos en staging, etc.

---

## Estructura del directorio de colección

Tras la configuración, tu carpeta de colección tiene este aspecto:

```
<tu-colección>/
  lore                          # el binario de loretools
  .loretools/
    config.json                 # configuración (creada automáticamente en el primer uso)
    keys/                       # pares de claves Ed25519 (solo si usas sincronización)
  library.json                  # tu biblioteca de referencias
  files/                        # PDFs y documentos archivados
  staging.json                  # referencias en staging
  staging/                      # archivos en staging
```

El agente siempre ejecuta `lore` desde esta carpeta, por lo que todas las rutas se resuelven correctamente sin ninguna configuración de PATH.

---

## Referencia de configuración

`.loretools/config.json` se crea automáticamente con valores predeterminados sensatos. Solo necesitas editarlo si quieres cambiar algo.

| Campo | Predeterminado | Qué controla |
|-------|----------------|--------------|
| `backend` | `"local"` | Backend de almacenamiento. Déjalo como `"local"` para uso con Co-Work. |
| `local.library_dir` | Carpeta de colección (CWD) | Dónde se almacenan `library.json`, `files/` y `staging/`. El valor predeterminado — la propia carpeta de colección — es correcto para Co-Work. |
| `apis.email` | (ninguno) | Tu correo para los límites de tasa del grupo de cortesía de Crossref y OpenAlex. Recomendado. |
| `llm.model` | `"claude-sonnet-4-6"` | Modelo Claude para extracción de texto de PDFs (PDFs escaneados). Requiere `ANTHROPIC_API_KEY`. |
| `citekey.pattern` | `"{author[2]}{year}"` | Patrón para las claves de referencia generadas. |

### Claves de API

Las claves de API nunca se almacenan en `config.json`. Configúralas como variables de entorno en tu sesión de Co-Work:

| Variable | Propósito |
|----------|-----------|
| `ANTHROPIC_API_KEY` | Extracción de PDFs mediante visión de Claude (PDFs escaneados) |
| `GBOOKS_API_KEY` | Google Books como fuente de búsqueda |
| `SEMANTIC_SCHOLAR_API_KEY` | Límites de tasa más altos en Semantic Scholar |

Sin estas claves, la herramienta degrada de forma elegante: la extracción con LLM se omite, Google Books se desactiva.

---

## Resolución de problemas

**`lore` no se encuentra tras la carga**
Asegúrate de que el zip fue descomprimido y que el archivo resultante se llama `lore` (no `scht-X.Y.Z-plataforma`). Dile al agente: "Lista los archivos en la carpeta de colección."

**Permiso denegado al ejecutar `lore`**
El binario necesita permiso de ejecución. Dile al agente: "Haz lore ejecutable con chmod +x."

**Configuración no encontrada o incompleta**
Ejecuta `./lore refs list` una vez — esto crea automáticamente `.loretools/config.json` si no existe.

**Las operaciones de biblioteca fallan en el primer uso**
`library.json` y `staging.json` se crean automáticamente en la primera escritura (primer `merge` o `add`). Es normal obtener resultados vacíos antes de eso.
