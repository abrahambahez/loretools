---
name: loretools-references
description: gestión de referencias en loretools — extraer metadatos de PDFs locales, poner referencias en staging, fusionarlas con la biblioteca, realizar CRUD completo sobre los registros y gestionar archivos vinculados a referencias (adjuntar, desvincular, mover, listar). Usa esto para cualquier tarea con loretools que implique extraer referencias de PDFs, agregarlas a la biblioteca, filtrar o buscar, actualizar o eliminar registros, el flujo staging→merge, o adjuntar/eliminar PDFs y EPUBs. Si el usuario hace algo con loretools relacionado con referencias que no sea exclusivamente configuración, usa esta skill.
---

## Conceptos

- **Staging**: área de exploración temporal. Las referencias viven aquí hasta que se promueven.
- **Biblioteca**: almacén de producción. Cada registro recibe un citekey asignado al hacer merge.
- **Flujo típico**: `lore extract <pdf>` → `lore staging stage` → revisar → `lore staging merge`

## Extracción

```sh
lore extract <ruta_archivo>
# Extrae metadatos de un PDF local usando pdfplumber.
# Si la confianza de extracción es baja, devuelve agent_extraction_needed: true —
# el agente debe entonces leer el PDF directamente y construir el JSON manualmente.
```

## Staging

```sh
lore staging stage '<json>' [--file <ruta>]
echo '<json>' | lore staging stage              # desde stdin

lore staging list-staged [--page N]

lore staging delete-staged <citekey>

lore staging merge [--omit clave1,clave2,...] [--allow-semantic]
# --allow-semantic: también promueve registros con uid_confidence=="semantic"
```

## CRUD de biblioteca

```sh
lore refs add '<json>'
echo '<json>' | lore refs add                   # desde stdin

lore refs get <citekey> [--uid <uid>]

lore refs update <citekey> '<json>'
echo '<json>' | lore refs update <citekey>      # desde stdin

lore refs rename <clave_antigua> <clave_nueva>

lore refs delete <citekey>

lore refs list [--page N]

lore refs filter [--query "<texto>"] [--author "<apellido>"] [--year AAAA] \
                 [--type <tipo-csl>] [--has-file] [--staging] [--page N]
# --type ejemplos: article-journal, book, chapter
# --staging: filtra registros en staging en lugar de la biblioteca
```

## Archivos

Los archivos se adjuntan a referencias de la **biblioteca** (no a las que están en staging). Cada referencia puede tener como máximo un archivo.

```sh
lore files attach <citekey> <ruta>
# Copia <ruta> a files/ y lo registra en la referencia.

lore files detach <citekey>
# Elimina la copia local y limpia el vínculo en la referencia.

lore files move <citekey> <nombre_destino>
# Renombra el archivo almacenado. nombre_destino es solo el nombre de archivo, sin ruta.

lore files reindex
# Repara rutas obsoletas si files/ fue reorganizado manualmente.

lore files get <citekey>
# Devuelve la ruta absoluta al archivo local.

lore files list [--page N]
```

Para adjuntar un archivo al ingresar una referencia: `lore staging stage '<json>' --file <ruta>` — `merge` lo mueve a files/.

## Campos clave de los modelos

**ReferenceRow** (resultados de list/filter): `citekey, title, authors, year, doi, uid, has_file, has_warnings`

**Reference** (registro completo): `id` (=citekey), `type` (CSL), `title`, `author: [{family, given}]`,
`issued: {date-parts: [[AAAA]]}`, `DOI`, `URL`, `uid`, `uid_confidence` ("authoritative"|"semantic")

**FileRow** (resultados de files list): `citekey, path, mime_type, size_bytes`

**FileRecord** (en Reference como `_file`): `path, mime_type, size_bytes, added_at`
