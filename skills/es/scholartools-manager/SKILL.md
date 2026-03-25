---
name: scholartools-manager
description: gestor de colecciones de scholartools — configuración inicial en Claude Co-Work, instalación del binario, creación de config y verificación al inicio de sesión. Usa esto cuando el usuario quiera configurar scholartools por primera vez, instalar el binario en un directorio de colección, crear o actualizar config.json, verificar que una colección esté operativa, o cuando algún comando falle porque falta el binario o la configuración.
---

Una **colección** es un directorio que contiene `scht`, `.scholartools/config.json` y los datos de la biblioteca del investigador. `scht` siempre opera relativo al directorio de trabajo actual (CWD) — sin configuración global, sin instalación en PATH.

## Configuración inicial (Claude Co-Work)

**Paso 1 — Instalar el binario**

El investigador ha subido un zip de la versión. Descomprimirlo y hacerlo ejecutable:

```bash
unzip scht-*.zip
chmod +x scht
```

Verificar que funciona:

```bash
./scht --version
```

**Paso 2 — Crear la configuración**

Ejecutar `scht` una vez desde el directorio de la colección para crear automáticamente `.scholartools/config.json` con valores por defecto:

```bash
./scht refs list
```

Esto crea `.scholartools/config.json` con `library_dir` apuntando al directorio de la colección (CWD). No se requiere ninguna otra configuración de rutas salvo que el usuario quiera un layout distinto.

**Paso 3 — Aplicar preferencias del usuario**

Si el usuario proporciona claves de API o quiere personalizar la configuración, editar `.scholartools/config.json`. Campos comunes:

```json
{
  "apis": { "email": "tu@email.com" },
  "llm": { "model": "claude-sonnet-4-6" }
}
```

Las claves de API se definen como variables de entorno (nunca en el config):

| Variable | Propósito |
|----------|-----------|
| `ANTHROPIC_API_KEY` | Extracción de PDF con Claude vision |
| `GBOOKS_API_KEY` | Fuente Google Books |

**Paso 4 — Verificar la colección**

```bash
./scht refs list
./scht staging list
```

Ambos deben devolver `{"ok": true, ...}`. La colección está lista.

## Estructura del directorio de colección tras la configuración

```
<colección>/
  scht                          # binario
  .scholartools/
    config.json                 # configuración (relativa al CWD, se crea automáticamente)
    keys/                       # pares de claves Ed25519 (solo sincronización)
  library.json                  # biblioteca de producción (creada al primer add/merge)
  files/                        # archivos PDF/documentos almacenados
  staging.json                  # referencias en staging
  staging/                      # archivos en staging
```

## Verificación al inicio de sesión

Al comenzar cada sesión de Co-Work, verificar que la colección es accesible:

```bash
./scht --version
./scht refs list
```

Si no se encuentra `scht`, el binario no fue subido o el directorio de trabajo no es correcto. Preguntar al usuario si la carpeta está montada y `scht` está presente.

## Referencia de configuración

Todos los campos excepto `backend` y `local` son opcionales.

| Campo | Por defecto | Descripción |
|-------|-------------|-------------|
| `backend` | `"local"` | Backend de almacenamiento. Siempre `"local"` salvo que se use sincronización S3. |
| `local.library_dir` | CWD | Raíz de todos los archivos de datos. Por defecto el directorio de colección. |
| `apis.email` | (ninguno) | Identifica peticiones a Crossref/OpenAlex para límites de tasa polite-pool. |
| `llm.model` | `"claude-sonnet-4-6"` | Modelo Claude para extracción PDF por visión. |
| `citekey.pattern` | `"{author[2]}{year}"` | Patrón de generación de citekeys. |

## Tokens del patrón de citekey

- `{author[N]}` — primeros N apellidos de autores unidos por `separator`
- `{year}` — año de 4 dígitos
- `etal` — se añade cuando los autores superan N
- `disambiguation_suffix`: `"letters"` (a/b/c) o `"title[1-9]"` (primeras N palabras del título)

## Flag global

```
./scht --plain <comando>   # salida en tabla legible en lugar de JSON
```

## Rutas calculadas (relativas a library_dir)

| Ruta | Propósito |
|------|-----------|
| `library.json` | Biblioteca de producción |
| `files/` | Archivos almacenados |
| `staging.json` | Referencias en staging |
| `staging/` | Archivos en staging |
| `peers/` | Registro de peers (solo sincronización) |
