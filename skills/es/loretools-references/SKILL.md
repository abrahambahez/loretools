---
name: loretools-references
description: gestión de referencias en loretools — descubrir referencias en APIs externas, obtener metadatos por DOI/arXiv/ISBN, extraer metadatos de PDFs locales, poner referencias en staging, fusionarlas con la biblioteca, realizar CRUD completo sobre los registros y gestionar archivos vinculados a referencias (vincular, desvincular, mover, listar). Usa esto para cualquier tarea con loretools que implique encontrar referencias, agregarlas a la biblioteca, filtrar o buscar, actualizar o eliminar registros, el flujo staging→merge, o adjuntar/eliminar PDFs y EPUBs. Si el usuario hace algo con loretools relacionado con referencias que no sea exclusivamente sincronización, usa esta skill.
---

## Conceptos

- **Staging**: área de exploración temporal. Las referencias viven aquí hasta que se promueven.
- **Biblioteca**: almacén de producción. Cada registro recibe un citekey asignado al hacer merge.
- **Flujo típico**: discover/fetch/extract → `lore staging stage` → revisar → `lore staging merge`

## Descubrimiento

```sh
lore discover "<consulta>" [--sources crossref,semantic_scholar,...] [--limit N]
# sources: crossref, semantic_scholar, arxiv, openalex, doaj, google_books

lore fetch <identificador>
# identificador: DOI, ID de arXiv o ISBN

lore extract <ruta_archivo>
# Requiere ANTHROPIC_API_KEY para el fallback LLM en PDFs escaneados
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

Los archivos se vinculan a referencias de la **biblioteca** (no a las que están en staging). Cada referencia puede tener como máximo un archivo.

```sh
lore files link <citekey> <ruta>
# Copia <ruta> al archivo y lo vincula a la referencia.

lore files unlink <citekey>
# Elimina la copia del archivo y limpia el vínculo en la referencia.

lore files move <citekey> <nombre_destino>
# Renombra el archivo almacenado. nombre_destino es solo el nombre de archivo, sin ruta.

lore files list [--page N]
```

Para adjuntar un archivo al ingresar una referencia: `lore staging stage '<json>' --file <ruta>` — `merge` lo mueve al archivo definitivo.

## Campos clave de los modelos

**ReferenceRow** (resultados de list/filter): `citekey, title, authors, year, doi, uid, has_file, has_warnings`

**Reference** (registro completo): `id` (=citekey), `type` (CSL), `title`, `author: [{family, given}]`,
`issued: {date-parts: [[AAAA]]}`, `DOI`, `URL`, `uid`, `uid_confidence` ("authoritative"|"semantic")

**FileRow** (resultados de files list): `citekey, path, mime_type, size_bytes`

**FileRecord** (en Reference como `_file`): `path, mime_type, size_bytes, added_at`
