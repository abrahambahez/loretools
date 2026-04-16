---
name: loretools-manager
description: gestor de colecciones loretools — configuración inicial en Claude Co-Work, instalación del binario, creación de config.json y verificación al inicio de sesión. Usa esto cuando el usuario quiera configurar loretools por primera vez, instalar el binario en un directorio de colección, crear o actualizar config.json, verificar que una colección esté operativa, o cuando algún comando de loretools falle porque el binario o la config no están presentes.
---

Una **colección** es un directorio que contiene `lore`, `.lore/config.json` y los datos de la biblioteca del investigador. `lore` siempre opera relativo al directorio de trabajo actual (CWD) — sin config global, sin necesidad de instalación en PATH.

## Configuración inicial (Claude Co-Work)

**Paso 1 — Instalar el binario**

El investigador ha subido un zip de la versión. Descomprimirlo y hacerlo ejecutable:

```bash
unzip lore-*.zip
chmod +x lore
```

Verificar que funciona:

```bash
./lore --version
```

**Paso 2 — Crear la config**

Ejecutar `lore` una vez desde el directorio de colección para auto-crear `.lore/config.json` con valores por defecto:

```bash
./lore refs list
```

Esto crea `.lore/config.json` con `library_dir` apuntando al directorio de colección (CWD). No se necesita más configuración de rutas salvo que el usuario quiera un layout diferente.

**Paso 3 — Aplicar preferencias del usuario (opcional)**

Si el usuario quiere personalizar la generación de citekeys, editar `.lore/config.json`:

```json
{
  "citekey": { "pattern": "{author[1]}{year}" }
}
```

**Paso 4 — Verificar la colección**

```bash
./lore refs list
./lore staging list-staged
```

Ambos deben devolver `{"ok": true, ...}`. La colección está lista.

## Estructura del directorio de colección tras la configuración

```
<colección>/
  lore                          # binario
  .lore/
    config.json                 # config (relativa a CWD, auto-creada)
  library.json                  # biblioteca de producción (creada al primer add/merge)
  files/                        # archivos PDF/documentos archivados
  staging.json                  # referencias en staging
  staging/                      # archivos en staging
```

## Verificación al inicio de sesión

Al comienzo de cada sesión Co-Work, verificar que la colección es accesible:

```bash
./lore --version
./lore refs list
```

Si no se encuentra `lore`, el binario no fue subido o el directorio de trabajo es incorrecto. Pedir al usuario que confirme que la carpeta está montada y que `lore` está presente.

## Referencia de config

| Campo | Valor por defecto | Descripción |
|-------|-------------------|-------------|
| `local.library_dir` | CWD | Raíz de todos los archivos de datos. Por defecto el directorio de colección. |
| `citekey.pattern` | `"{author[2]}{year}"` | Patrón de generación de citekeys. |
| `citekey.separator` | `"_"` | Separador entre tokens de autor. |
| `citekey.etal` | `"_etal"` | Sufijo añadido cuando los autores superan el límite del patrón. |
| `citekey.disambiguation_suffix` | `"letters"` | `"letters"` (a/b/c) o `"title[1-9]"` (primeras N palabras del título). |

## Tokens del patrón de citekey

- `{author[N]}` — los primeros N apellidos de autor unidos por `separator`
- `{year}` — año de 4 dígitos

## Flag global

```
./lore --plain <comando>   # salida en tabla legible en lugar de JSON
```

## Rutas calculadas (relativas a library_dir)

| Ruta | Propósito |
|------|-----------|
| `library.json` | Biblioteca de producción |
| `files/` | Archivos archivados |
| `staging.json` | Referencias en staging |
| `staging/` | Archivos en staging |
